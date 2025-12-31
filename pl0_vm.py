from pl0_types import OpCode, Instruction

class VM:
    def __init__(self, code, input_data=[]):
        self.code = code
        self.stack = [0] * 1000
        self.pc = 0   # Program Counter
        self.bp = 0   # Base Pointer (Current stack frame)
        self.sp = -1  # Stack Pointer
        self.input_buffer = input_data
        self.output_buffer = []

    def base(self, l):
        """Find base L levels down"""
        b = self.bp
        while l > 0:
            b = self.stack[b] # 静态链在栈帧的 offset 0 处 (取决于具体实现)
            l -= 1
        return b

    def run(self):
        print("Running VM...")
        try:
            while self.pc < len(self.code):
                i = self.code[self.pc]
                self.pc += 1
                
                if i.f == OpCode.LIT:
                    self.sp += 1
                    self.stack[self.sp] = i.a
                
                elif i.f == OpCode.LOD: # Load var to stack top
                    self.sp += 1
                    # 简化：假设静态链处理正确
                    self.stack[self.sp] = self.stack[self.base(i.l) + i.a]

                elif i.f == OpCode.STO:
                    self.stack[self.base(i.l) + i.a] = self.stack[self.sp]
                    self.sp -= 1

                elif i.f == OpCode.CAL: # Call procedure
                    # 生成新栈帧：SL, DL, RA
                    self.stack[self.sp + 1] = self.base(i.l) # Static Link
                    self.stack[self.sp + 2] = self.bp       # Dynamic Link
                    self.stack[self.sp + 3] = self.pc       # Return Address
                    self.bp = self.sp + 1
                    self.pc = i.a
                
                elif i.f == OpCode.INT: # Alloc stack
                    self.sp += i.a
                
                elif i.f == OpCode.JMP:
                    self.pc = i.a
                
                elif i.f == OpCode.JPC:
                    if self.stack[self.sp] == 0:
                        self.pc = i.a
                    self.sp -= 1
                
                elif i.f == OpCode.WRT:
                    self.output_buffer.append(str(self.stack[self.sp]))
                    self.sp -= 1
                
                elif i.f == OpCode.RED:
                    # 读取输入
                    if self.input_buffer:
                        value = self.input_buffer.pop(0)
                    else:
                        value = 0  # 如果没有输入，默认为0
                    self.sp += 1
                    self.stack[self.sp] = value
                    
                elif i.f == OpCode.OPR:
                    if i.a == 0: # Return
                        if self.bp == 0: break
                        self.sp = self.bp - 1
                        self.pc = self.stack[self.sp + 3]
                        self.bp = self.stack[self.sp + 2]
                    elif i.a == 1: # 取负
                        self.stack[self.sp] = -self.stack[self.sp]
                    elif i.a == 2: # +
                        self.stack[self.sp - 1] += self.stack[self.sp]
                        self.sp -= 1
                    elif i.a == 3: # -
                        self.stack[self.sp - 1] -= self.stack[self.sp]
                        self.sp -= 1
                    elif i.a == 4: # *
                        self.stack[self.sp - 1] *= self.stack[self.sp]
                        self.sp -= 1
                    elif i.a == 5: # /
                        if self.stack[self.sp] == 0:
                            raise RuntimeError("除数为零")
                        self.stack[self.sp - 1] //= self.stack[self.sp] # 整除
                        self.sp -= 1
                    elif i.a == 6: # odd
                        self.stack[self.sp] = self.stack[self.sp] % 2
                    elif i.a == 8: # =
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] == self.stack[self.sp] else 0
                        self.sp -= 1
                    elif i.a == 9: # # (不等于)
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] != self.stack[self.sp] else 0
                        self.sp -= 1
                    elif i.a == 10: # <
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] < self.stack[self.sp] else 0
                        self.sp -= 1
                    elif i.a == 11: # >= (大于等于)
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] >= self.stack[self.sp] else 0
                        self.sp -= 1
                    elif i.a == 12: # >
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] > self.stack[self.sp] else 0
                        self.sp -= 1
                    elif i.a == 13: # <= (小于等于)
                        self.stack[self.sp - 1] = 1 if self.stack[self.sp - 1] <= self.stack[self.sp] else 0
                        self.sp -= 1
        except Exception as e:
            return f"Runtime Error: {e}"
        
        return "\n".join(self.output_buffer)