// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(TotalLoop)
@8192
D=A;
//n for the id of registers
@n
M=D
@KBD
D=M
@WhiteLoop
D;JEQ

(BlackLoop)
@n
D=M-1
@SCREEN
A=A+D
M=-1
@TotalLoop
D;JEQ
@n
M=M-1
@BlackLoop
0;JMP

(WhiteLoop)
@n
D=M-1
@SCREEN
A=A+D
M=0
@TotalLoop
D;JEQ
@n
M=M-1
@WhiteLoop
0;JMP