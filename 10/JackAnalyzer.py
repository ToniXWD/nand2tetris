import os
import re
import argparse
import glob

JackKeyWords = {'class', 'constructor', 'method', 'function',
                'boolean', 'int', 'char', 'void',
                'var', 'static', 'field',
                'let', 'do', 'if', 'else', 'while', 'return',
                'true', 'false', 'null',
                'this'}
JackSymbols = {'{', '}', '(', ')', '[', ']', '.', ',',
               ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'}
JackReturnType = {'boolean', 'int', 'char', 'void'}
JackVarType = {'boolean', 'int', 'char'}
JackStatementType = {'if', 'let', 'while', 'do', 'return'}
JackOp = {'+', '-', '*', '/', '&', '|', '<', '>', '='}
JackUOp = {'-', '~'}


def typeJudge(token):
    if token in JackKeyWords:
        return token, 'keyword'
    elif token in JackSymbols:
        return token, 'symbol'
    else:
        return token, 'identifier'


class JackTokenizer:
    def __init__(self, filePath):
        self.words = []
        self.lineIds = []
        self.tokens = []
        with open(filePath) as fp:
            multiComment = False
            for lineid, line in enumerate(fp):
                lineid = lineid + 1
                line = line.strip()
                if line == "":  # 跳过空行
                    continue
                if line.startswith("//"):  # 跳过单行注释
                    continue
                if line.startswith("/**"):  # 多行注释开始
                    multiComment = True
                    if line.endswith("*/"):  # 多行注释可能也只注释了一行
                        multiComment = False
                    continue
                if multiComment:  # 判断多行注释是否结束，并跳过该行
                    if line.endswith("*/"):
                        multiComment = False
                    continue
                if "//" in line:
                    line = line.split("//")[0].strip()
                if '\"' in line:
                    all_index = [r.span()[0] for r in re.finditer('\"', line)]
                    isQuate = False
                    lastIndex = 0
                    for i in all_index:
                        if isQuate:
                            target = line[lastIndex:i + 1]
                            self.words.append((target, lineid))
                            lastIndex = i + 1
                            isQuate = False
                        else:
                            target = line[lastIndex:i].split()
                            toExtend = [(token, lineid) for token in target]
                            self.words.extend(toExtend)
                            lastIndex = i
                            isQuate = True

                    toExtend = [(token, lineid) for token in line[all_index[-1] + 1:].split()]
                    self.words.extend(toExtend)
                else:
                    toExtend = [(token, lineid) for token in line.split()]
                    self.words.extend(toExtend)
        self.words2tokens()

    def words2tokens(self):
        for word, lineid in self.words:
            if word in JackKeyWords or word in JackSymbols:
                self.tokens.append((word, lineid))
            else:
                word2list = self.parseComplexWords(word, [])
                self.tokens.extend([(i, lineid) for i in word2list])

    def parseComplexWords(self, word: str, word2tokens: list):
        if word == '':
            return word2tokens
        if word in JackKeyWords or word in JackSymbols:
            word2tokens.append(word)
            return word2tokens
        if word.startswith('('):  # 以(开始的表达式，先记录(
            word2tokens.append('(')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith('['):  # 以[开始的表达式，先记录[
            word2tokens.append('[')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith(')'):  # 以(开始的表达式，先记录)
            word2tokens.append(')')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith(']'):  # 以[开始的表达式，先记录]
            word2tokens.append(']')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith('\"'):  # ""包裹的字符串
            word2tokens.append(word)
            return word2tokens
        if word[0].isalnum():  # 处理自定义变量，即字母和数字组成的部分
            item = ''
            while word[0].isalnum():
                item += word[0]
                word = word[1:]
                if word == '':
                    break
            word2tokens.append(item)
            return self.parseComplexWords(word, word2tokens)
        if word.startswith('.'):
            word2tokens.append('.')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith('~'):
            word2tokens.append('~')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)
        if word.startswith('-'):
            word2tokens.append('-')
            word = word[1:]
            return self.parseComplexWords(word, word2tokens)


class JackAnalyzer:
    def __init__(self, inputFile, outFile):
        self.lineId = None
        self.tokens = None
        self.i = 0
        self.input = inputFile
        self.outFile = None
        self.fp = None
        self.compileFile = None

    def file2tokens(self, inputFile):
        j = JackTokenizer(inputFile)
        tokensIds = j.tokens
        self.tokens = [token[0] for token in tokensIds]
        self.lineId = [token[1] for token in tokensIds]

    def writeTag(self, tagType: str, tagBegin: bool):
        if tagBegin:
            self.fp.write('<{}>\n'.format(tagType))
        else:
            self.fp.write('</{}>\n'.format(tagType))

    def writeSimpleTag(self, text: str, tagType: str):
        self.fp.write('<{}> '.format(tagType))
        self.fp.write(text)
        self.fp.write(' </{}>\n'.format(tagType))

    def writeToken(self, assertToken=True, expJudge=None, asText: str = None, termType=None):
        token, tType = typeJudge(self.tokens[self.i])
        if termType is not None:
            tType = termType
        if assertToken:
            if expJudge is not None:
                if type(expJudge) == str:
                    if token != expJudge:
                        raise RuntimeError(asText + " Error in line {}".format(self.lineId[self.i]))
                else:
                    if token not in expJudge:
                        raise RuntimeError(asText + " Error in line {}".format(self.lineId[self.i]))
        else:
            if expJudge is not None:
                if type(expJudge) == str:
                    if tType != expJudge:
                        raise RuntimeError(asText + " Error in line {}".format(self.lineId[self.i]))
                else:
                    if tType not in expJudge:
                        raise RuntimeError(asText + " Error in line {}".format(self.lineId[self.i]))
        self.writeSimpleTag(token, tType)
        self.i += 1

    def termTyoe(self):
        index = self.i
        token1, tType1 = typeJudge(self.tokens[index])
        token2, tType2 = typeJudge(self.tokens[index + 1])

        if token1 == '(':
            return 'expression'
        if token1 in JackUOp:
            return 'unary'
        if str.isdigit(token1):
            return 'integerConstant'
        if '\"' in token1:
            return 'stringConstant'
        if token1 in ('true', 'false', 'null', 'this'):
            return 'keywordConstant'
        if tType1 == 'identifier':
            if token2 in ('.', '('):
                return 'call'
            if token2 == '[':
                return 'varSub'
            else:
                return 'var'
        return False

    def compileSingle(self):
        if os.path.isfile(self.compileFile):
            if self.outFile is None:
                outName = 'my' + os.path.basename(self.compileFile).split('.')[0] + '.xml'
                self.outFile = os.path.join(os.path.dirname(self.compileFile), outName)
        self.file2tokens(self.compileFile)
        self.fp = open(self.outFile, 'w')
        self.compilationEngine()
        self.fp.close()

    def compile(self):
        if os.path.isfile(self.input):
            self.compileFile = self.input
            self.compileSingle()
        elif os.path.isdir(self.input):
            JackFiles = glob.glob(os.path.join(self.input, '*.jack'))
            for file in JackFiles:
                self.compileFile = file
                self.outFile = None
                self.i = 0
                self.compileSingle()


    def compilationEngine(self):
        token, tType = typeJudge(self.tokens[self.i])
        assert token == 'class', "A Jack file must begin with the keyword class"
        self.writeTag('class', True)
        self.CompileClass()
        self.writeTag('class', False)

    def CompileClass(self):
        self.writeToken()  # <keyword> class </keyword>
        self.writeToken(False, 'identifier', "There must be an identifier after keyword class")
        # <identifier> SquareGame </identifier>

        self.writeToken(True, '{', "There must be a { after class name")
        # <symbol> { </symbol>

        self.CompileClassVarDec()
        self.CompileSubroutine()

        token, tType = typeJudge(self.tokens[self.i])
        if token != '}':
            raise RuntimeError("A class must end with a symbol }" + " Error in line {}".format(self.lineId[self.i]))
        self.writeSimpleTag(token, tType)  # 此处 self.i 不需要自增

    def CompileClassVarDec(self):
        token, tType = typeJudge(self.tokens[self.i])
        if token not in ('field', 'static'):
            return

        while token in ('field', 'static'):
            self.writeTag('classVarDec', True)
            self.writeToken()
            # 写入如： <keyword> field </keyword>

            token, tType = typeJudge(self.tokens[self.i])
            if (token not in ('boolean', 'int', 'char')) and (tType != 'identifier'):
                raise RuntimeError(
                    "class var type must be one of 'boolean, int, char' or an identifier" + " Error in line {}".format(
                        self.lineId[self.i]))

            self.i += 1
            self.writeSimpleTag(token, tType)  # 写入如 <keyword> int </keyword>

            token, tType = typeJudge(self.tokens[self.i])
            if tType != 'identifier':
                raise RuntimeError(
                    "class var name must be an identifier" + " Error in line {}".format(self.lineId[self.i]))
            while tType == 'identifier':
                self.i += 1
                self.writeSimpleTag(token, tType)  # 写入如 <identifier> a </identifier>
                token, tType = typeJudge(self.tokens[self.i])
                if token == ',':
                    self.writeToken()
                    # 写入如 <symbol> , </symbol>
                    token, tType = typeJudge(self.tokens[self.i])
                elif token == ';':
                    self.writeToken()
                    # 写入如 <symbol> ; </symbol>
                    token, tType = typeJudge(self.tokens[self.i])
                    break
                else:
                    raise RuntimeError("classVarDec error")
            self.writeTag('classVarDec', False)

    def CompileSubroutine(self):
        token, tType = typeJudge(self.tokens[self.i])
        if token not in ('method', 'function', 'constructor'):
            return

        while token in ('method', 'function', 'constructor'):
            self.writeTag('subroutineDec', True)
            self.writeToken()  # 写入如 <keyword> function </keyword> 或 <keyword> constructor </keyword>

            token, tType = typeJudge(self.tokens[self.i])
            if (token not in JackReturnType) and tType != 'identifier':
                raise RuntimeError("return type must be one of 'boolean', 'int', 'char', 'void' or be an identifier"
                                   + " Error in line {}".format(self.lineId[self.i]))
            self.writeToken()  # 写入如 <keyword> void </keyword> 或 <identifier> SquareGame </identifier>

            self.writeToken(False, 'identifier', "function or method's name must be an identifier")
            # 写入如 <identifier> main </identifier>

            self.writeToken(True, '(', "There must be a parameter list after the name of the function or method")
            self.CompileParameterList()
            self.writeToken(True, ')', "There must be a ) to end a parameter list")
            self.CompileSubroutinebody()
            token, tType = typeJudge(self.tokens[self.i])
            self.writeTag('subroutineDec', False)

    def CompileSubroutinebody(self):
        self.writeTag('subroutineBody', True)
        self.writeToken(True, '{', "body of a function or method must begin with {")  # <symbol> { </symbol>

        self.CompileVarDec()  # 定义局部变量
        self.CompileStatements()  # statements

        self.writeToken(True, '}', "body of a function or method must end with }")  # <symbol> } </symbol>
        self.writeTag('subroutineBody', False)

    def CompileParameterList(self):
        self.writeTag('parameterList', True)  # 写入如 <parameterList>

        token, tType = typeJudge(self.tokens[self.i])
        while True:
            if token == ')':
                break
            if token not in JackVarType and tType != 'identifier':
                raise RuntimeError("Must declare variable's type" + " Error in line {}".format(self.lineId[self.i]))
            self.writeToken()  # 写入如 <keyword> int </keyword>

            self.writeToken(False, 'identifier', "Variable's name must be an identifier")
            # <identifier> Ay </identifier>

            token, tType = typeJudge(self.tokens[self.i])
            if token == ',':
                self.writeToken()  # <identifier> , </identifier>
                token, tType = typeJudge(self.tokens[self.i])

        self.writeTag('parameterList', False)  # 写入如 <parameterList>

    def CompileVarDec(self):
        token, tType = typeJudge(self.tokens[self.i])
        if token != 'var':
            return

        while token == 'var':
            self.writeTag('varDec', True)
            self.writeToken()  # <keyword> var </keyword>

            token, tType = typeJudge(self.tokens[self.i])
            if token not in JackVarType and tType != 'identifier':
                raise RuntimeError("local variable must be given a proper type")
            self.writeToken()  # <keyword> char </keyword>

            self.writeToken(False, 'identifier', "local variable must be given a proper name")
            # <identifier> a </identifier>

            token, tType = typeJudge(self.tokens[self.i])
            while token == ',':
                self.writeToken()  # <symbol> , </symbol>
                self.writeToken(False, 'identifier', "local variable must be given a proper name")
                # <identifier> b </identifier>
                token, tType = typeJudge(self.tokens[self.i])
            self.writeToken(True, ';', "Variable declaration must end with the symbol ;")  # <symbol> ; </symbol>
            self.writeTag('varDec', False)
            token, tType = typeJudge(self.tokens[self.i])

    def CompileStatements(self):
        self.writeTag('statements', True)
        token, tType = typeJudge(self.tokens[self.i])
        if token not in JackStatementType:
            raise RuntimeError("Unsupported statement! A statement must begin with 'if', 'let', 'while', 'do', 'return'. " + "Error in line {}".format(self.lineId[self.i]))
        while token in JackStatementType:
            if token == 'do':
                self.CompileDo()
            elif token == 'let':
                self.CompileLet()
            elif token == 'if':
                self.CompileIf()
            elif token == 'while':
                self.CompileWhile()
            elif token == 'return':
                self.CompileReturn()
            token, tType = typeJudge(self.tokens[self.i])
        self.writeTag('statements', False)

    def CompileSubRoutineCall(self):
        self.writeToken(False, 'identifier', "There must be an illegal identifier after keyword do")
        # <identifier> square </identifier>

        token, tType = typeJudge(self.tokens[self.i])
        while token == '.':
            self.writeToken()  # <symbol> . </symbol>
            self.writeToken(False, 'identifier', "There must be an illegal identifier after symbol . ")
            # <identifier> dispose </identifier>
            token, tType = typeJudge(self.tokens[self.i])
        self.writeToken(True, '(', "SubRoutineCall must have (...)")  # <symbol> ( </symbol>
        self.CompileExpressionList()
        self.writeToken(False, 'symbol')  # <symbol> ) </symbol>

    def CompileExpressionList(self):
        self.writeTag('expressionList', True)

        token, tType = typeJudge(self.tokens[self.i])
        while self.termTyoe():  # 如果不是合法的term，就不是合法的expression，即返回false
            self.CompileExpression()  # first expression
            token, tType = typeJudge(self.tokens[self.i])
            while token == ',':
                self.writeToken()  # <symbol> , </symbol>
                self.CompileExpression()  # more expressions
                token, tType = typeJudge(self.tokens[self.i])

        self.writeTag('expressionList', False)

    def CompileDo(self):
        self.writeTag('doStatement', True)
        self.writeToken()  # <keyword> do </keyword>
        self.CompileSubRoutineCall()
        self.writeToken(True, ';', "Do statement must end with ;")  # <keyword> ; </keyword>
        self.writeTag('doStatement', False)

    def CompileLet(self):
        self.writeTag('letStatement', True)
        self.writeToken()  # <keyword> let </keyword>
        self.writeToken(False, 'identifier', "There must be an illegal identifier after keyword let")
        # <identifier> square </identifier>

        token, tType = typeJudge(self.tokens[self.i])
        if token == '[':
            self.writeToken()  # <symbol> [ </symbol>
            self.CompileExpression()
            self.writeToken(True, ']', "There must be an ']' after previous '['")
            # <symbol> ] </symbol>
        self.writeToken(True, '=', "There must be a '=' in a let statement")  # <symbol> = </symbol>
        self.CompileExpression()
        self.writeToken(True, ';', "One statement must end with ;")  # <symbol> ; </symbol>
        self.writeTag('letStatement', False)

    def CompileWhile(self):
        self.writeTag('whileStatement', True)
        self.writeToken()  # <keyword> while </keyword>
        self.writeToken(True, '(', 'There must be a (...) after keyword while')
        self.CompileExpression()
        self.writeToken(True, ')', 'There must be a ) after previous (')
        self.writeToken(True, '{', 'There must be a {...} after while(...)')
        self.CompileStatements()
        self.writeToken(True, '}', 'There must be a } after previous {')
        self.writeTag('whileStatement', False)

    def CompileReturn(self):
        self.writeTag('returnStatement', True)
        self.writeToken()  # <keyword> return </keyword>
        token, tType = typeJudge(self.tokens[self.i])
        while token != ';':
            self.CompileExpression()
            token, tType = typeJudge(self.tokens[self.i])
        self.writeToken(True, ';', "return statement must end with ;")
        self.writeTag('returnStatement', False)

    def CompileIf(self):
        self.writeTag('ifStatement', True)
        self.writeToken()  # <keyword> if </keyword>
        self.writeToken(True, '(', "There must be (...) after keyword if")  # <symbol> ( </symbol>
        self.CompileExpression()
        self.writeToken(True, ')', "There must be a ) after previous '('")  # <symbol> ) </symbol>
        self.writeToken(True, '{', "There must be {...} after if(...)")  # <symbol> { </symbol>
        self.CompileStatements()
        self.writeToken(True, '}', "There must be a ) after previous '{'")  # <symbol> } </symbol>

        token, tType = typeJudge(self.tokens[self.i])
        if token == 'else':
            self.writeToken()  # <keyword> else </keyword>
            self.writeToken(True, '{', "There must be {...} after else")  # <symbol> { </symbol>
            self.CompileStatements()
            self.writeToken(True, '}', "There must be a ) after previous '{'")  # <symbol> } </symbol>
        self.writeTag('ifStatement', False)

    def CompileExpression(self):
        self.writeTag('expression', True)
        self.CompileTerm()
        token, tType = typeJudge(self.tokens[self.i])
        while token in JackOp:
            self.writeToken()  # <symbol> + </symbol>
            self.CompileTerm()
            token, tType = typeJudge(self.tokens[self.i])
        self.writeTag('expression', False)

    def CompileTerm(self):
        termType = self.termTyoe()
        if not termType:
            return
        self.writeTag('term', True)
        if termType == 'expression':
            self.writeToken()  # <symbol> ( </symbol>
            self.CompileExpression()
            self.writeToken()  # <symbol> ) </symbol>
        elif termType in ('integerConstant', 'stringConstant'):
            self.writeToken(termType=termType)  # <integerConstant> 1 </integerConstant>
        elif termType in ('var', 'keywordConstant'):
            self.writeToken()  # <identifier> direction </identifier>
        elif termType == 'unary':
            self.writeToken()  # <identifier> ~ </identifier>
            self.CompileTerm()
        elif termType == 'call':
            self.CompileSubRoutineCall()
        elif termType == 'varSub':
            self.writeToken()  # <identifier> array </identifier>
            self.writeToken()  # <symbol> [ </symbol>
            self.CompileExpression()
            self.writeToken()  # <symbol> ] </symbol>
        self.writeTag('term', False)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='input jack file or input directory')
    parser.add_argument('--output', default=None, help='output xml file')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    a1 = JackAnalyzer(args.input, args.output)
    a1.compile()
