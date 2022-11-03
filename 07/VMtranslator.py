import argparse
import os


class VMTranslator(object):
    def __init__(self, inputFile, outfile=None):
        super().__init__()
        self.input = inputFile
        if outfile is not None:
            self.output = outfile
        else:
            self.output = os.path.join(os.path.dirname(inputFile), os.path.basename(inputFile).split('.')[0] + '.asm')

        self.Symbol4 = {}
        self.Symbol4['local'] = 'LCL'
        self.Symbol4['argument'] = 'ARG'
        self.Symbol4['this'] = 'THIS'
        self.Symbol4['that'] = 'THAT'
        self.EQ0C = 0
        self.EG0C = 0
        self.EL0C = 0

        self.Static = os.path.basename(inputFile).split('.')[0]

    def constructor(self):
        fi = open(self.input, "r")
        fo = open(self.output, 'w')
        for lineId, line in enumerate(fi):
            line = line.strip()
            if line == '' or line[:2] == '//':
                continue
            fo.write("\n//"+line+'\n')

            # 长度为1，表示算术运算符
            if line.split().__len__() == 1:
                fo.write(self.arithmetic2string(line, lineId))
            # push
            elif line.split()[0] == "push":
                fo.write(self.push2string(line, lineId))
            elif line.split()[0] == "pop":
                fo.write(self.pop2string(line, lineId))
        fo.close()
        fi.close()

    def arithmetic2string(self,line, lineId):
        if line == 'add':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M+D\n"
        if line == 'sub':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n"
        if line == 'neg':
            return "@SP\nA=M-1\nM=-M\n"
        if line == 'eq':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EQ0_{}\nD;JNE\n@SP\nA=M-1\nM=-1\n(EQ0_{})\n".format(self.EQ0C, self.EQ0C)
            self.EQ0C += 1
            return exp
        if line == 'gt':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EG0_{}\nD;JLE\n@SP\nA=M-1\nM=-1\n(EG0_{})\n".format(self.EG0C, self.EG0C)
            self.EG0C += 1
            return exp
        if line == 'lt':
            exp = "@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\nM=0\n@EL0_{}\nD;JGE\n@SP\nA=M-1\nM=-1\n(EL0_{})\n".format(self.EL0C, self.EL0C)
            self.EL0C += 1
            return exp
        if line == 'and':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M&D\n"
        if line == 'or':
            return "@SP\nAM=M-1\nD=M\nA=A-1\nM=M|D\n"
        if line == 'not':
            return "@SP\nA=M-1\nM=!M\n"
        else:
            raise SyntaxError("Arithmetic error! From line {}:{}".format(lineId+1, line))

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
            exp = "Push segment error! From line {}:{}".format(lineId+1, line)
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
            exp = "Pop segment error! From line {}:{}".format(lineId+1, line)
            raise SyntaxError(exp)
        return rstr


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
    VMT.constructor()
    print("Translating the vm code successfully!")


if __name__ == '__main__':
    main()
