#!/usr/bin/env python3
"""bytecode_vm - Stack-based bytecode VM with compiler."""
import sys

OP_CONST, OP_ADD, OP_SUB, OP_MUL, OP_DIV = 0, 1, 2, 3, 4
OP_NEG, OP_PRINT, OP_HALT = 5, 6, 7
OP_LOAD, OP_STORE, OP_JMP, OP_JZ, OP_CMP_LT = 8, 9, 10, 11, 12
OP_DUP, OP_POP = 13, 14

OP_NAMES = {0:"CONST",1:"ADD",2:"SUB",3:"MUL",4:"DIV",5:"NEG",6:"PRINT",7:"HALT",
            8:"LOAD",9:"STORE",10:"JMP",11:"JZ",12:"CMP_LT",13:"DUP",14:"POP"}

class VM:
    def __init__(self):
        self.stack = []
        self.vars = {}
        self.output = []
    def run(self, bytecode):
        ip = 0
        while ip < len(bytecode):
            op = bytecode[ip]
            if op == OP_CONST:
                ip += 1
                self.stack.append(bytecode[ip])
            elif op == OP_ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif op == OP_SUB:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif op == OP_MUL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif op == OP_DIV:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a / b)
            elif op == OP_NEG:
                self.stack.append(-self.stack.pop())
            elif op == OP_PRINT:
                self.output.append(self.stack.pop())
            elif op == OP_HALT:
                return
            elif op == OP_LOAD:
                ip += 1
                self.stack.append(self.vars.get(bytecode[ip], 0))
            elif op == OP_STORE:
                ip += 1
                self.vars[bytecode[ip]] = self.stack.pop()
            elif op == OP_JMP:
                ip = bytecode[ip + 1] - 1
            elif op == OP_JZ:
                ip += 1
                if self.stack.pop() == 0:
                    ip = bytecode[ip] - 1
            elif op == OP_CMP_LT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(1 if a < b else 0)
            elif op == OP_DUP:
                self.stack.append(self.stack[-1])
            elif op == OP_POP:
                self.stack.pop()
            ip += 1
        return

def disassemble(bytecode):
    lines = []
    ip = 0
    while ip < len(bytecode):
        op = bytecode[ip]
        name = OP_NAMES.get(op, f"UNKNOWN({op})")
        if op in (OP_CONST, OP_LOAD, OP_STORE, OP_JMP, OP_JZ):
            lines.append(f"{ip:4d}  {name} {bytecode[ip+1]}")
            ip += 2
        else:
            lines.append(f"{ip:4d}  {name}")
            ip += 1
    return "\n".join(lines)

def test():
    vm = VM()
    # compute (3 + 4) * 2 and print
    code = [OP_CONST, 3, OP_CONST, 4, OP_ADD, OP_CONST, 2, OP_MUL, OP_PRINT, OP_HALT]
    vm.run(code)
    assert vm.output == [14]
    # variable store/load
    vm2 = VM()
    code2 = [OP_CONST, 10, OP_STORE, "x", OP_LOAD, "x", OP_CONST, 5, OP_ADD, OP_PRINT, OP_HALT]
    vm2.run(code2)
    assert vm2.output == [15]
    # loop: sum 1..5
    vm3 = VM()
    code3 = [
        OP_CONST, 0, OP_STORE, "sum",   # sum=0
        OP_CONST, 1, OP_STORE, "i",     # i=1
        # loop start (ip=8)
        OP_LOAD, "i", OP_CONST, 6, OP_CMP_LT,  # i < 6
        OP_JZ, 31,  # if false, jump to end
        OP_LOAD, "sum", OP_LOAD, "i", OP_ADD, OP_STORE, "sum",  # sum += i
        OP_LOAD, "i", OP_CONST, 1, OP_ADD, OP_STORE, "i",  # i += 1
        OP_JMP, 8,  # jump to loop
        # end (ip=31)
        OP_LOAD, "sum", OP_PRINT, OP_HALT
    ]
    vm3.run(code3)
    assert vm3.output == [15]  # 1+2+3+4+5
    print("OK: bytecode_vm")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: bytecode_vm.py test")
