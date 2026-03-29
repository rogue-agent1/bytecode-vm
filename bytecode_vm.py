#!/usr/bin/env python3
"""bytecode_vm - Stack-based bytecode virtual machine."""
import sys, struct

# Opcodes
PUSH = 0x01; POP = 0x02; DUP = 0x03; SWAP = 0x04
ADD = 0x10; SUB = 0x11; MUL = 0x12; DIV = 0x13; MOD = 0x14; NEG = 0x15
EQ = 0x20; NE = 0x21; LT = 0x22; GT = 0x23; LE = 0x24; GE = 0x25
AND = 0x30; OR = 0x31; NOT = 0x32
JMP = 0x40; JZ = 0x41; JNZ = 0x42
LOAD = 0x50; STORE = 0x51
CALL = 0x60; RET = 0x61
PRINT = 0x70; HALT = 0xFF

OP_NAMES = {v: k for k, v in dict(
    PUSH=0x01, POP=0x02, DUP=0x03, SWAP=0x04,
    ADD=0x10, SUB=0x11, MUL=0x12, DIV=0x13, MOD=0x14, NEG=0x15,
    EQ=0x20, NE=0x21, LT=0x22, GT=0x23, LE=0x24, GE=0x25,
    AND=0x30, OR=0x31, NOT=0x32,
    JMP=0x40, JZ=0x41, JNZ=0x42,
    LOAD=0x50, STORE=0x51,
    CALL=0x60, RET=0x61,
    PRINT=0x70, HALT=0xFF
).items()}

class VM:
    def __init__(self, code, stack_size=1024):
        self.code = code
        self.stack = [0] * stack_size
        self.sp = 0
        self.ip = 0
        self.vars = {}
        self.call_stack = []
        self.output = []
        self.halted = False
    
    def push(self, v):
        self.stack[self.sp] = v
        self.sp += 1
    
    def pop(self):
        self.sp -= 1
        return self.stack[self.sp]
    
    def peek(self):
        return self.stack[self.sp - 1]
    
    def read_i32(self):
        v = struct.unpack_from("!i", self.code, self.ip)[0]
        self.ip += 4
        return v
    
    def run(self, max_steps=100000):
        steps = 0
        while not self.halted and self.ip < len(self.code) and steps < max_steps:
            op = self.code[self.ip]
            self.ip += 1
            steps += 1
            
            if op == PUSH: self.push(self.read_i32())
            elif op == POP: self.pop()
            elif op == DUP: self.push(self.peek())
            elif op == SWAP:
                a, b = self.pop(), self.pop()
                self.push(a); self.push(b)
            elif op == ADD: self.push(self.pop() + self.pop())
            elif op == SUB:
                b, a = self.pop(), self.pop()
                self.push(a - b)
            elif op == MUL: self.push(self.pop() * self.pop())
            elif op == DIV:
                b, a = self.pop(), self.pop()
                self.push(a // b if b != 0 else 0)
            elif op == MOD:
                b, a = self.pop(), self.pop()
                self.push(a % b if b != 0 else 0)
            elif op == NEG: self.push(-self.pop())
            elif op == EQ: self.push(int(self.pop() == self.pop()))
            elif op == NE: self.push(int(self.pop() != self.pop()))
            elif op == LT:
                b, a = self.pop(), self.pop()
                self.push(int(a < b))
            elif op == GT:
                b, a = self.pop(), self.pop()
                self.push(int(a > b))
            elif op == LE:
                b, a = self.pop(), self.pop()
                self.push(int(a <= b))
            elif op == GE:
                b, a = self.pop(), self.pop()
                self.push(int(a >= b))
            elif op == AND: self.push(int(bool(self.pop()) and bool(self.pop())))
            elif op == OR: self.push(int(bool(self.pop()) or bool(self.pop())))
            elif op == NOT: self.push(int(not self.pop()))
            elif op == JMP: self.ip = self.read_i32()
            elif op == JZ:
                addr = self.read_i32()
                if self.pop() == 0: self.ip = addr
            elif op == JNZ:
                addr = self.read_i32()
                if self.pop() != 0: self.ip = addr
            elif op == LOAD:
                idx = self.read_i32()
                self.push(self.vars.get(idx, 0))
            elif op == STORE:
                idx = self.read_i32()
                self.vars[idx] = self.pop()
            elif op == CALL:
                addr = self.read_i32()
                self.call_stack.append(self.ip)
                self.ip = addr
            elif op == RET:
                self.ip = self.call_stack.pop()
            elif op == PRINT:
                self.output.append(self.pop())
            elif op == HALT:
                self.halted = True
        return self.output

def assemble(*instructions):
    code = bytearray()
    for inst in instructions:
        if isinstance(inst, int):
            code.append(inst)
        elif isinstance(inst, tuple):
            code.append(inst[0])
            code.extend(struct.pack("!i", inst[1]))
    return bytes(code)

def test():
    # 2 + 3
    code = assemble((PUSH, 2), (PUSH, 3), ADD, PRINT, HALT)
    vm = VM(code)
    assert vm.run() == [5]
    
    # (10 - 3) * 2
    code = assemble((PUSH, 10), (PUSH, 3), SUB, (PUSH, 2), MUL, PRINT, HALT)
    vm = VM(code)
    assert vm.run() == [14]
    
    # Variables: x=5, y=10, print x+y
    code = assemble(
        (PUSH, 5), (STORE, 0),
        (PUSH, 10), (STORE, 1),
        (LOAD, 0), (LOAD, 1), ADD, PRINT, HALT
    )
    vm = VM(code)
    assert vm.run() == [15]
    
    # Loop: sum 1..5
    # var[0] = sum, var[1] = i
    code = assemble(
        (PUSH, 0), (STORE, 0),   # sum = 0
        (PUSH, 1), (STORE, 1),   # i = 1
        # loop start (ip=10):
        (LOAD, 1), (PUSH, 6), LT,  # i < 6
        (JZ, 73),                   # if not, jump to end
        (LOAD, 0), (LOAD, 1), ADD, (STORE, 0),  # sum += i
        (LOAD, 1), (PUSH, 1), ADD, (STORE, 1),  # i++
        (JMP, 20),                  # goto loop
        # end (ip=73):
        (LOAD, 0), PRINT, HALT
    )
    vm = VM(code)
    assert vm.run() == [15]  # 1+2+3+4+5
    
    # Comparison
    code = assemble((PUSH, 5), (PUSH, 3), GT, PRINT, HALT)
    vm = VM(code)
    assert vm.run() == [1]
    
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: bytecode_vm.py test")
