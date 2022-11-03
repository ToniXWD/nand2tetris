import argparse
import os
import glob


def delComment(x):
    x = x.strip()
    if x[:2] == "//":
        return ''
    else:
        return x.split("//")[0] + '\n'


class VMTranslator(object):
    def __init__(self, inputFile, outfile=None):
        super().__init__()
        self.input = inputFile

        self.fileName = os.path.basename(inputFile)
        self.fileNames = None

        if outfile is not None:
            self.output = outfile
        else:
            self.output = os.path.join(os.path.dirname(inputFile), self.fileName + '.asm')

        self.Symbol4 = {'local': 'LCL', 'argument': 'ARG', 'this': 'THIS', 'that': 'THAT'}
        self.EQ0C = 0
        self.EG0C = 0
        self.EL0C = 0

        self.Static = os.path.basename(inputFile).split('.')[0]

        self.currentFunc = ''
        self.funcCallCounter = {}

    def complie(self):
        if os.path.isfile(self.input):
            fo = open(self.output, 'w')
            self.fileName = self.input
            self.constructor(fo)
        elif os.path.isdir(self.input):
            self.output = os.path.join(self.input, os.path.basename(self.input) + ".asm")
            fo = open(self.output, 'w')
            self.fileNames = glob.glob(os.path.join(self.input, "*.vm"))
            fileBaseNames = list(map(os.path.basename, self.fileNames))
            fileDict = dict(zip(fileBaseNames, self.fileNames))

            if "Sys.vm" in fileDict.keys():
                self.fileName = fileDict["Sys.vm"]
                self.Static = os.path.basename(self.fileName).split('.')[0]

                with open("./initCode.txt", 'r', encoding='utf8') as fp:
                    f = fp.readlines()
                    f = map(delComment, f)
                    rtr = ''.join(f)
                fo.write(rtr)

                self.constructor(fo)
                del fileDict["Sys.vm"]
            elif "Main.vm" in fileDict.keys():
                self.fileName = fileDict["Main.vm"]
                self.Static = os.path.basename(self.fileName).split('.')[0]
                self.constructor(fo)
                del fileDict["Main.vm"]

            for vmFile, vmPath in fileDict.items():
                self.fileName = vmPath
                self.Static = vmFile.split('.')[0]
                self.constructor(fo)

            fo.close()

    def constructor(self, fo):
        fi = open(self.fileName, "r")
        for lineId, line in enumerate(fi):
            # line = line.strip()
            # if line == '' or line[:2] == '//':
            #     continue
            line = delComment(line).split('\n')[0]
            line = line.strip()
            if line == '':
                continue
            fo.write("\n//" + line + '\n')

            # 长度为1且不为return，表示算术运算符
            if line.split().__len__() == 1 and line != "return":
                fo.write(self.arithmetic2string(line, lineId))
            # push
            elif line.split()[0] == "push":
                fo.write(self.push2string(line, lineId))
            elif line.split()[0] == "pop":
                fo.write(self.pop2string(line, lineId))
            elif line.split()[0] in ('goto', 'if-goto', 'label'):
                fo.write(self.branch2string(line, lineId))
            elif line.split()[0] == "function":
                fo.write(self.function2string(line, lineId))
            elif line.split()[0] == "return":
                fo.write(self.return2string())
            elif line.split()[0] == "call":
                fo.write(self.call2string(line, lineId))
        fi.close()

    def arithmetic2string(self, line, lineId):
        if line == 'add':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M+D\n"
        if line == 'sub':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n"
        if line == 'neg':
            return "@SP\nA=M-1\nM=-M\n"
        if line == 'eq':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EQ0_{}\nD;JNE\n@SP\nA=M-1\nM=-1\n(EQ0_{})\n".format(self.EQ0C,
                                                                                                             self.EQ0C)
            self.EQ0C += 1
            return exp
        if line == 'gt':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EG0_{}\nD;JLE\n@SP\nA=M-1\nM=-1\n(EG0_{})\n".format(self.EG0C,
                                                                                                             self.EG0C)
            self.EG0C += 1
            return exp
        if line == 'lt':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EL0_{}\nD;JGE\n@SP\nA=M-1\nM=-1\n(EL0_{})\n".format(self.EL0C,
                                                                                                             self.EL0C)
            self.EL0C += 1
            return exp
        if line == 'and':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M&D\n"
        if line == 'or':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M|D\n"
        if line == 'not':
            return "@SP\nA=M-1\nM=!M\n"
        else:
            exp = "Arithmetic error in file{}, line {}:{}".format(self.fileName, lineId + 1, line)
            raise SyntaxError(exp)

    def push2string(self, line, lineId):
        rstr = ''
        _, segment, idx = line.split()
        if segment == 'constant':
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@SP\nA=M\nM=D\n'
            rstr += '@SP\nM=M+1\n'
        elif segment in self.Symbol4.keys():
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@' + self.Symbol4[segment] + '\n'
            rstr += 'A=M+D\n'
            rstr += 'D=M\n'
            rstr += '@SP\nA=M\nM=D\n'
            rstr += '@SP\nM=M+1\n'
        elif segment == 'static':
            rstr += '@' + self.Static + '.' + idx + '\n'
            rstr += 'D=M\n'
            rstr += '@SP\nA=M\nM=D\n'
            rstr += '@SP\nM=M+1\n'
        elif segment == 'temp':
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@5\nA=A+D\n'
            rstr += 'D=M\n'
            rstr += '@SP\nA=M\nM=D\n'
            rstr += '@SP\nM=M+1\n'
        elif segment == 'pointer':
            if int(idx) not in (0, 1):
                exp2 = "Pop/Push's index of pointer must be 0 or 1!"
                raise SyntaxError(exp2)
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@3\nA=A+D\n'  # @3 means @THIS
            rstr += 'D=M\n'
            rstr += '@SP\nA=M\nM=D\n'
            rstr += '@SP\nM=M+1\n'
        else:
            exp = "Push segment error in file{}, line {}:{}".format(self.fileName, lineId + 1, line)
            raise SyntaxError(exp)
        return rstr

    def pop2string(self, line, lineId):
        rstr = ''
        _, segment, idx = line.split()
        # No pop constant operation
        if segment in self.Symbol4.keys():
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@' + self.Symbol4[segment] + '\n'
            rstr += 'D=M+D\n'
            rstr += '@R15\nM=D\n'  # self define
            rstr += '@SP\nAM=M-1\nD=M\n'
            rstr += '@R15\nA=M\nM=D\n'
        elif segment == 'static':
            rstr += '@' + self.Static + '.' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@R15\nM=D\n'
            rstr += '@SP\nAM=M-1\nD=M\n'
            rstr += '@R15\nA=M\nM=D\n'
        elif segment == 'temp':
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@5\nD=A+D\n'
            rstr += '@R15\nM=D\n'
            rstr += '@SP\nAM=M-1\n'
            rstr += 'D=M\n'
            rstr += '@R15\nA=M\nM=D\n'
        elif segment == 'pointer':
            if int(idx) not in (0, 1):
                exp2 = "Pop/Push's index of pointer must be 0 or 1!"
                raise SyntaxError(exp2)
            rstr += '@' + idx + '\n'
            rstr += 'D=A\n'
            rstr += '@3\nD=A+D\n'  # @3 means @THIS
            rstr += '@R15\nM=D\n'
            rstr += '@SP\nAM=M-1\nD=M\n'
            rstr += '@R15\nA=M\nM=D\n'
        else:
            exp = "Pop segment error in file{}, line {}:{}".format(self.fileName, lineId + 1, line)
            raise SyntaxError(exp)
        return rstr

    def branch2string(self, line, lineId):
        splitList = line.split()
        if splitList[0] == 'label':
            return '({}${})\n'.format(self.currentFunc, splitList[1])
        elif splitList[0] == 'goto':
            return '@{}${}\nD;JMP\n'.format(self.currentFunc, splitList[1])
        elif splitList[0] == 'if-goto':
            return '@SP\nAM=M-1\nD=M\n@{}${}\nD;JNE\n'.format(self.currentFunc, splitList[1])

    def function2string(self, line, lineId):
        splitList = line.split()
        self.currentFunc = splitList[1]
        rstr = "({})\n".format(self.currentFunc)
        for i in range(int(splitList[2])):
            rstr += '@SP\nA=M\nM=0\n@SP\nM=M+1\n'
        return rstr

    @staticmethod
    def return2string():
        with open("./returnCode.txt", 'r', encoding='utf8') as fp:
            f = fp.readlines()
            f = map(delComment, f)
            rtr = ''.join(f)
        return rtr

    def call2string(self, line, lineId):
        splitList = line.split()
        functionName = splitList[1]
        if functionName not in self.funcCallCounter.keys():
            self.funcCallCounter[functionName] = 0
        else:
            self.funcCallCounter[functionName] += 1
        newLabel = "@End${}${}\n".format(functionName, self.funcCallCounter[functionName])

        with open("callSaveRetLclArgThisThat.txt", 'r', encoding='utf8') as fp:
            f = fp.readlines()
            f = map(delComment, f)
            rtr = ''.join(f)
            callSaveRetLclArgThisThat = ''.join(rtr)

        # 将ARG指向当前SP的前5 + splitList[2]个位置，5表示栈中储存原函数的state：returnAdress、LCL、ARG、THIS、THAT， splitList[2]表示参数的数量
        newARG = "@{}\n".format(5 + int(splitList[2]))
        newARG += "D=A\n@SP\nD=M-D\n@ARG\nM=D\n"

        newLCL = "@SP\nD=M\n@LCL\nM=D\n"

        callCommand = "@{}\n0;JMP\n".format(functionName)

        Label = "(End${}${})\n".format(functionName, self.funcCallCounter[functionName])

        return newLabel + callSaveRetLclArgThisThat + newARG + newLCL + callCommand + Label


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="Source vm code")
    parser.add_argument('--output', help="Output file's path")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.output is not None:
        VMT = VMTranslator(args.input, args.output)
    else:
        VMT = VMTranslator(args.input)
    VMT.complie()
    print("Translating the vm code successfully!")


if __name__ == '__main__':
    main()
