import argparse

def compare(file1, file2):
    f1 = open(file1,'r')
    f2 = open(file2,'r')
    text1 = f1.readlines()
    text2 = f2.readlines()
    for id, (t1, t2) in enumerate(zip(text1, text2)):
        if t1 != t2:
            print("Different lines:{}".format(id+1))
            print("     file1: {}".format(t1))
            print("     file2: {}".format(t2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file1')
    parser.add_argument('file2')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    compare(args.file1, args.file2)

if __name__ == '__main__':
    main()
