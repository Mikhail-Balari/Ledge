"""
Ledge Native Compiler — ledge_lang.compiler
============================================
Compiles Ledge → LLVM IR → native binary / WASM / serverless.

Usage:
    # Get LLVM IR (always works, no LLVM needed)
    from ledge_lang.compiler import compile_to_ir
    ir = compile_to_ir("define x as 42\\nshow x")
    
    # Compile to native binary (needs clang)
    from ledge_lang.compiler import compile_to_native
    binary = compile_to_native("show 42", "out")
    
    # Compile to WASM (needs emcc or clang wasm32)
    from ledge_lang.compiler import compile_to_wasm
    wasm = compile_to_wasm("show 42", "out.wasm")
"""
from .codegen import compile_to_ir, LLVMCodegen
from .targets import (compile_to_native, compile_to_wasm, compile_to_js,
                      compile_to_serverless, auto_compile, TargetNotAvailable)

__all__ = [
    'compile_to_ir', 'LLVMCodegen',
    'compile_to_native', 'compile_to_wasm', 'compile_to_js',
    'compile_to_serverless', 'auto_compile', 'TargetNotAvailable',
]
