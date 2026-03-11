#!/usr/bin/env python3
"""bytecode_vm - Stack-based bytecode virtual machine with compiler.

Usage: python bytecode_vm.py [--demo]
"""
from enum import IntEnum

class Op(IntEnum):
    CONST = 0; ADD = 1; SUB = 2; MUL = 3; DIV = 4; MOD = 5
    NEG = 6; NOT = 7; EQ = 8; LT = 9; GT = 10
    LOAD = 11; STORE = 12; POP = 13; DUP = 14
    JMP = 15; JZ = 16; JNZ = 17
    CALL = 18; RET = 19; PRINT = 20; HALT = 21
    LOAD_GLOBAL = 22; STORE_GLOBAL = 23

class Frame:
    def __init__(self, code, ip=0, locals_=None, ret_addr=None):
        self.code = code; self.ip = ip
        self.locals = locals_ or {}; self.ret_addr = ret_addr

class VM:
    def __init__(self):
        self.stack = []; self.frames = []; self.globals = {}
        self.output = []; self.steps = 0

    def run(self, code, max_steps=10000):
        self.frames = [Frame(code)]
        while self.steps < max_steps:
            frame = self.frames[-1]
            if frame.ip >= len(frame.code):
                break
            op = frame.code[frame.ip]; frame.ip += 1; self.steps += 1
            if op == Op.CONST:
                self.stack.append(frame.code[frame.ip]); frame.ip += 1
            elif op == Op.ADD: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a+b)
            elif op == Op.SUB: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a-b)
            elif op == Op.MUL: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a*b)
            elif op == Op.DIV: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a//b if b else 0)
            elif op == Op.MOD: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(a%b if b else 0)
            elif op == Op.NEG: self.stack.append(-self.stack.pop())
            elif op == Op.NOT: self.stack.append(int(not self.stack.pop()))
            elif op == Op.EQ: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(int(a==b))
            elif op == Op.LT: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(int(a<b))
            elif op == Op.GT: b,a = self.stack.pop(), self.stack.pop(); self.stack.append(int(a>b))
            elif op == Op.LOAD:
                name = frame.code[frame.ip]; frame.ip += 1
                self.stack.append(frame.locals.get(name, 0))
            elif op == Op.STORE:
                name = frame.code[frame.ip]; frame.ip += 1
                frame.locals[name] = self.stack.pop()
            elif op == Op.LOAD_GLOBAL:
                name = frame.code[frame.ip]; frame.ip += 1
                self.stack.append(self.globals.get(name, 0))
            elif op == Op.STORE_GLOBAL:
                name = frame.code[frame.ip]; frame.ip += 1
                self.globals[name] = self.stack.pop()
            elif op == Op.POP: self.stack.pop()
            elif op == Op.DUP: self.stack.append(self.stack[-1])
            elif op == Op.JMP: frame.ip = frame.code[frame.ip]
            elif op == Op.JZ:
                target = frame.code[frame.ip]; frame.ip += 1
                if not self.stack.pop(): frame.ip = target
            elif op == Op.JNZ:
                target = frame.code[frame.ip]; frame.ip += 1
                if self.stack.pop(): frame.ip = target
            elif op == Op.CALL:
                target_code = frame.code[frame.ip]; frame.ip += 1
                nargs = frame.code[frame.ip]; frame.ip += 1
                args = {}
                for i in range(nargs):
                    args[f"arg{nargs-1-i}"] = self.stack.pop()
                self.frames.append(Frame(target_code, 0, args, (len(self.frames)-1, frame.ip)))
            elif op == Op.RET:
                ret_val = self.stack.pop() if self.stack else 0
                self.frames.pop()
                self.stack.append(ret_val)
            elif op == Op.PRINT:
                val = self.stack.pop()
                self.output.append(str(val))
                print(f"  > {val}")
            elif op == Op.HALT:
                break
        return self.stack[-1] if self.stack else None

def disassemble(code):
    lines = []; ip = 0
    while ip < len(code):
        op = code[ip]
        if isinstance(op, Op):
            name = op.name
            if op in (Op.CONST, Op.LOAD, Op.STORE, Op.LOAD_GLOBAL, Op.STORE_GLOBAL, Op.JMP, Op.JZ, Op.JNZ):
                lines.append(f"  {ip:4d}: {name:15s} {code[ip+1]}"); ip += 2
            elif op == Op.CALL:
                lines.append(f"  {ip:4d}: {name:15s} <fn> nargs={code[ip+2]}"); ip += 3
            else:
                lines.append(f"  {ip:4d}: {name}"); ip += 1
        else:
            ip += 1
    return "\n".join(lines)

def main():
    print("=== Bytecode VM ===\n")
    # Program: compute factorial(10)
    # fact(n): if n <= 1 return 1; return n * fact(n-1)
    fact_code = [
        Op.LOAD, "arg0",        # 0: load n
        Op.CONST, 1,            # 2: push 1
        Op.GT,                  # 4: n > 1?
        Op.JZ, 18,              # 5: if not, jump to return 1
        Op.LOAD, "arg0",        # 7: load n
        Op.LOAD, "arg0",        # 9: load n
        Op.CONST, 1,            # 11: push 1
        Op.SUB,                 # 13: n-1
        Op.CALL, None, 1,       # 14: call fact(n-1) — patch target
        Op.MUL,                 # 17: n * fact(n-1)
        Op.RET,                 # 18 (after mul) or base case:
        Op.CONST, 1,            # 19: push 1
        Op.RET,                 # 21
    ]
    # Fix jump target for base case
    fact_code[6] = 19
    # Self-reference for recursion
    fact_code[15] = fact_code

    main_code = [
        Op.CONST, 10,           # push 10
        Op.CALL, fact_code, 1,  # call fact(10)
        Op.DUP,                 # dup for print
        Op.PRINT,               # print result
        Op.HALT,
    ]

    print("Disassembly (main):")
    print(disassemble(main_code))
    print()

    vm = VM()
    result = vm.run(main_code)
    print(f"\nResult: {result}")
    print(f"Steps: {vm.steps}")
    assert result == 3628800, f"Expected 3628800, got {result}"
    print("✓ fact(10) = 3628800")

    # Fibonacci
    print("\n--- Fibonacci ---")
    fib_code = [
        Op.LOAD, "arg0", Op.CONST, 2, Op.LT, Op.JZ, 12,
        Op.LOAD, "arg0", Op.RET,  # base: return n
        # recursive
        Op.LOAD, "arg0", Op.CONST, 1, Op.SUB,
        Op.CALL, None, 1,  # fib(n-1)
        Op.LOAD, "arg0", Op.CONST, 2, Op.SUB,
        Op.CALL, None, 1,  # fib(n-2)
        Op.ADD, Op.RET,
    ]
    fib_code[6] = 10  # jump to recursive case
    fib_code[17] = fib_code
    fib_code[24] = fib_code

    for n in range(10):
        vm2 = VM()
        result = vm2.run([Op.CONST, n, Op.CALL, fib_code, 1, Op.HALT])
        print(f"  fib({n}) = {result} ({vm2.steps} steps)")

if __name__ == "__main__":
    main()
