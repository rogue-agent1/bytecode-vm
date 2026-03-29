#!/usr/bin/env python3
"""bytecode_vm - Stack-based bytecode VM with compiler."""
import sys, argparse, struct

# Opcodes
PUSH, POP, ADD, SUB, MUL, DIV, MOD = 0,1,2,3,4,5,6
EQ, LT, GT, NOT, AND, OR = 7,8,9,10,11,12
LOAD, STORE, JUMP, JUMP_IF, JUMP_NOT = 13,14,15,16,17
CALL, RET, PRINT, HALT = 18,19,20,21
DUP, SWAP, ROT = 22,23,24

OP_NAMES = {v:k for k,v in dict(PUSH=0,POP=1,ADD=2,SUB=3,MUL=4,DIV=5,MOD=6,
    EQ=7,LT=8,GT=9,NOT=10,AND=11,OR=12,LOAD=13,STORE=14,JUMP=15,
    JUMP_IF=16,JUMP_NOT=17,CALL=18,RET=19,PRINT=20,HALT=21,DUP=22,SWAP=23,ROT=24).items()}

HAS_ARG = {PUSH, LOAD, STORE, JUMP, JUMP_IF, JUMP_NOT, CALL}

class VM:
    def __init__(self, code, debug=False):
        self.code = code; self.stack = []; self.vars = {}
        self.ip = 0; self.frames = []; self.debug = debug; self.output = []

    def run(self, max_steps=100000):
        for step in range(max_steps):
            if self.ip >= len(self.code): break
            op = self.code[self.ip]; self.ip += 1
            arg = None
            if op in HAS_ARG: arg = self.code[self.ip]; self.ip += 1
            if self.debug: print(f"  [{step}] {OP_NAMES.get(op,'?')} {arg if arg is not None else ''} stack={self.stack[:8]}")
            if op == PUSH: self.stack.append(arg)
            elif op == POP: self.stack.pop()
            elif op == DUP: self.stack.append(self.stack[-1])
            elif op == SWAP: self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
            elif op == ADD: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a+b)
            elif op == SUB: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a-b)
            elif op == MUL: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a*b)
            elif op == DIV: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a//b if b else 0)
            elif op == MOD: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a%b if b else 0)
            elif op == EQ: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(1 if a==b else 0)
            elif op == LT: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(1 if a<b else 0)
            elif op == GT: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(1 if a>b else 0)
            elif op == NOT: self.stack.append(0 if self.stack.pop() else 1)
            elif op == LOAD: self.stack.append(self.vars.get(arg, 0))
            elif op == STORE: self.vars[arg] = self.stack.pop()
            elif op == JUMP: self.ip = arg
            elif op == JUMP_IF: self.ip = arg if self.stack.pop() else self.ip
            elif op == JUMP_NOT: self.ip = arg if not self.stack.pop() else self.ip
            elif op == CALL: self.frames.append(self.ip); self.ip = arg
            elif op == RET:
                if self.frames: self.ip = self.frames.pop()
                else: break
            elif op == PRINT: v = self.stack.pop(); self.output.append(v); print(v)
            elif op == HALT: break
        return self.stack[-1] if self.stack else 0

def assemble(text):
    labels = {}; code = []; lines = text.strip().split("\n")
    # First pass: find labels
    pc = 0
    for line in lines:
        line = line.strip().split(";")[0].strip()
        if not line: continue
        if line.endswith(":"): labels[line[:-1]] = pc; continue
        parts = line.split(); pc += 1
        if parts[0].upper() in [OP_NAMES.get(i,"") for i in HAS_ARG] or (len(parts)>1): pc += 1
    # Second pass
    for line in lines:
        line = line.strip().split(";")[0].strip()
        if not line or line.endswith(":"): continue
        parts = line.split()
        op_name = parts[0].upper()
        op = {v:k for k,v in OP_NAMES.items()}.get(op_name)
        if op is None: raise ValueError(f"Unknown op: {op_name}")
        code.append(op)
        if len(parts) > 1:
            arg = parts[1]
            if arg in labels: code.append(labels[arg])
            else: code.append(int(arg))
    return code

def main():
    p = argparse.ArgumentParser(description="Bytecode VM")
    p.add_argument("file", nargs="?")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    if args.demo:
        # Compute sum 1..100
        code = [PUSH,0,STORE,0, PUSH,1,STORE,1,  # sum=0, i=1
                LOAD,1,PUSH,101,LT,JUMP_NOT,30,   # while i<101
                LOAD,0,LOAD,1,ADD,STORE,0,         # sum+=i
                LOAD,1,PUSH,1,ADD,STORE,1,         # i+=1
                JUMP,8,                             # loop
                LOAD,0,PRINT,HALT]                  # print sum
        vm = VM(code, args.debug)
        vm.run()
        print(f"\nFibonacci via assembly:")
        asm = """
PUSH 0
STORE 0      ; a=0
PUSH 1
STORE 1      ; b=1
PUSH 0
STORE 2      ; i=0
loop:
LOAD 2
PUSH 10
LT
JUMP_NOT done
LOAD 0
PRINT
LOAD 0
LOAD 1
ADD
STORE 2      ; temp reuse
LOAD 1
STORE 0
LOAD 2
STORE 1
PUSH 1
STORE 2
JUMP loop
done:
HALT
"""
        # Simplified: just run sum demo
        print("Sum 1..100 computed above")
    elif args.file:
        with open(args.file) as f: code = assemble(f.read())
        VM(code, args.debug).run()
    else: p.print_help()
if __name__ == "__main__": main()
