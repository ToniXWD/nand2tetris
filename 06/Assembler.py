import os
import json
import argparse

class Assembler(object):
    """
    self.fileDir: 目标文件路径
    self.syTable: 预先定义的标识符、自定义label、自定义variable的字典
    self.outDir: 输出文件路径
    self.ram: 储存variable的RAM地址
    """

    def __init__(self, fileDir, outDir=None):
        self.fileDir = fileDir
        self.syTable = {}

        for i in range(16):
            self.syTable['R' + str(i)] = i

        self.syTable['SCREEN'] = 16384
        self.syTable['KBD'] = 24576

        self.syTable['SP'] = 0
        self.syTable['LCL'] = 1
        self.syTable['ARG'] = 2
        self.syTable['THIS'] = 3
        self.syTable['THAT'] = 4

        self.ram = 16

        if outDir is None:
            self.outDir = os.path.join(os.path.dirname(fileDir), os.path.basename(fileDir).split('.')[0] + '.hack')
        else:
            self.outDir = outDir

        with open("./Cinstruction.json", 'r') as fp:
            self.command = json.load(fp)

    def parser(self, line, id=None):
        # instruction A
        if line[0] == '@':
            Address = line[1:]
            # @数字
            if Address.isdigit():
                address = bin(int(Address))[2:]
                return '0' * (16 - len(address)) + address + '\n'
            # @variable
            elif Address in self.syTable.keys():
                address = bin(self.syTable[Address])[2:]
                return '0' * (16 - len(address)) + address + '\n'
            else:
                self.syTable[Address] = self.ram
                self.ram += 1
                address = bin(self.syTable[Address])[2:]
                return '0' * (16 - len(address)) + address + '\n'
            # else:
            #     print(line)
            #     raise SyntaxError("A instruction Error! Source code is '{}' in line{}".format(line, id))

        # instruction C
        else:
            if '=' in line:
                dest, cj = line.split('=')
                dest = dest.strip()
                if ';' in cj: # ？
                    comp, jump = cj.split(';')
                    comp, jump = comp.strip(), jump.strip()
                else: # 简单赋值，，形如 D=A
                    comp = cj.strip()
                    jump = "null"
            else: # 形如 0;JMP
                comp, jump = line.split(';')
                comp = comp.strip()
                jump = jump.strip()
                dest = "null"

            if dest not in self.command["dest"].keys():
                raise SyntaxError("Dest syntax error! Source code is '{}' in line {}".format(line, id))
            destO = self.command["dest"][dest]

            if jump not in self.command["jump"].keys():
                raise SyntaxError("Jump syntax error! Source code is '{}' in line{}".format(line, id))
            jumpO = self.command["jump"][jump]

            if comp in self.command["comp"]["0"].keys():
                compA = "0"
            elif comp in self.command["comp"]["1"].keys():
                compA = "1"
            else:
                raise SyntaxError("Dest syntax error! Source code is '{}' in line{}".format(line, id))

            compB = self.command["comp"][compA][comp]

            return "111" + compA + compB + destO + jumpO +'\n'

    def readline(self, stage):
        fi = open(self.fileDir, "r")
        if stage == 1:
            realID = 0
            for line in fi:
                line = line.strip()
                if line == '' or line[:2] == '//':
                    continue
                if line[0] == '(':
                    if line[1:-1] not in self.syTable.keys():
                        self.syTable[line[1:-1]] = realID
                else:
                    realID += 1
        if stage == 2:
            fo = open(self.outDir, 'w')
            for id, line in enumerate(fi):
                line = line.strip()
                line = line.split('//')[0]
                if line == '' or line[:2] == '//' or line[0] == '(':
                    continue
                writeStr = self.parser(line, id + 1)
                fo.write(writeStr)
            fo.close()
        fi.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Assemble *.asm to *.hack script"
    )
    parser.add_argument('input_file', help="Source asm code")
    parser.add_argument('--output', help="Output file's path")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.output is not None:
        ass = Assembler(args.input_file, args.output)
    else:
        ass = Assembler(args.input_file)
    ass.readline(1)
    ass.readline(2)
    print("Assemble successfully!")


if __name__ == '__main__':
    main()




