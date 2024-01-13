from enum import Enum
import os
from typing import Dict, Mapping, List, Tuple, Set

# Uses bit-twiddling to represent a character set.
# For example, if you construct with 'A-Za-z_0-9',
# Then has will return true for all alpha-numerics.
class CharSet():
    def __init__(self, s:str) -> None:
        self.bits = 0
        i = 0
        for i in range(len(s)):
            if s[i] == '-' and i > 0 and i + 1 < len(s):
                span = ord(s[i + 1]) - ord(s[i - 1])
                if span > 0:
                    for j in range(1, span):
                        self.bits |= (1 << (ord(s[i - 1]) + j))
                else:
                    for j in range(1, -span):
                        self.bits |= (1 << (ord(s[i - 1]) - j))
            else:
                self.bits |= (1 << (ord(s[i])))

    # Returns True iff the specified character is in this CharSet
    def has(self, s:str) -> bool:
        return self.bits & (1 << ord(s)) > 0
                



_built_in_cpp_tokens = [
    'back',
    'break',
    'bool',
    'case',
    'catch',
    'char',
    'cin',
    'class',
    'clear',
    'compare',
    'config',
    'continue',
    'cout',
    'default',
    'define',
    'delete',
    'double',
    'endif',
    'else',
    'endl',
    'false',
    'float',
    'flush',
    'for',
    'getline',
    'if',
    'ifndef',
    'include',
    'int',
    'memcpy',
    'new',
    'nullptr',
    'push_back',
    'private',
    'protected',
    'public',
    'return',
    'runtime_error',
    'size',
    'size_t',
    'sleep',
    'std',
    'stoi',
    'string',
    'strcpy',
    'strlen',
    'struct',
    'switch',
    'throw',
    'this',
    'true',
    'try',
    'usleep',
    'vector',
    'virtual',
    'void',
    'while',
]
built_in_cpp_tokens = { v:(i+1) for i,v in enumerate(_built_in_cpp_tokens) }

_built_in_java_tokens = [
    'abstract',
    'ActionEvent',
    'ActionListener',
    'addActionListener',
    'addMouseListener',
    'append',
    'ArrayList',
    'break',
    'boolean',
    'BufferedImage',
    'BufferedReader',
    'BufferedWriter',
    'case',
    'catch',
    'char',
    'charAt',
    'class',
    'Color',
    'compare',
    'continue',
    'default',
    'delete',
    'double',
    'Double',
    'drawImage',
    'else',
    'equals',
    'Exception',
    'extends',
    'false',
    'FileReader',
    'FileWriter',
    'fillRect',
    'final',
    'finally',
    'for',
    'getButton',
    'getHeight',
    'getWidth',
    'Graphics',
    'if',
    'IllegalArgumentException',
    'implements',
    'import',
    'int',
    'Integer',
    'IOException',
    'java',
    'JFrame',
    'JPanel',
    'KeyEvent',
    'KeyListener',
    'length',
    'main',
    'MAX_VALUE',
    'MouseEvent',
    'MouseListener',
    'new',
    'null',
    'Override',
    'Point',
    'private',
    'protected',
    'public',
    'read',
    'return',
    'RuntimeException',
    'setColor',
    'size',
    'sleep',
    'static',
    'String',
    'StringBuilder',
    'substring',
    'super',
    'System',
    'switch',
    'toString',
    'Thread',
    'throw',
    'this',
    'true',
    'try',
    'util',
    'void',
    'while',
    'write',
]
built_in_java_tokens = { v:(i+1) for i,v in enumerate(_built_in_java_tokens) }

_built_in_javascript_tokens = [
    'addEventListener',
    'Array',
    'async',
    'await',
    'break',
    'bool',
    'callable',
    'case',
    'catch',
    'char',
    'class',
    'concat',
    'console',
    'const',
    'continue',
    'Date',
    'default',
    'delete',
    'document',
    'else',
    'false',
    'fetch',
    'finally',
    'floor',
    'for',
    'function',
    'getElementById',
    'if',
    'Image',
    'innerHTML',
    'int',
    'interface',
    'keyCode',
    'keyDown',
    'keyUp',
    'length',
    'let',
    'log',
    'Math',
    'max',
    'min',
    'new',
    'null',
    'number',
    'onclick',
    'onClick',
    'onTimer',
    'pop',
    'Promise',
    'prototype',
    'push',
    'resolve',
    'return',
    'setInterval',
    'setTimeout',
    'slice',
    'splice',
    'string',
    'switch',
    'then',
    'throw',
    'this',
    'true',
    'try',
    'TypeError',
    'var',
    'void',
    'while',
    'yield',
]
built_in_javascript_tokens = { v:(i+1) for i,v in enumerate(_built_in_javascript_tokens) }

class CppState(Enum):
    whitespace = 1
    line_comment = 2
    block_comment = 3
    identifier = 4
    number = 5
    string = 6
    symbol = 7

def tokenize_cpp_like_file(s:str, built_in_tokens:Mapping[str,int]) -> str:
    # Make a bunch of useful character sets
    alpha = CharSet('A-Za-z_')
    alpha_num = CharSet('A-Za-z_0-9')
    num = CharSet('0-9')
    whitespace = CharSet(' \t\r\n')
    endline = CharSet('\r\n')

    # Tokenize the string
    output = []
    state = CppState.whitespace
    tok = ''
    while len(s) > 0:
        if state == CppState.whitespace:
            # Skip the whitespace
            while len(s) > 0 and whitespace.has(s[0]):
                s = s[1:]

            # Determine what is coming next
            tok = ''
            if len(s) > 0:
                if alpha.has(s[0]):
                    state = CppState.identifier
                elif num.has(s[0]):
                    state = CppState.number
                elif s[0] == '"':
                    state = CppState.string
                elif len(s) > 1 and s[0] == '/' and s[1] == '/':
                    state = CppState.line_comment
                elif len(s) > 1 and s[0] == '/' and s[1] == '*':
                    state = CppState.block_comment
                else:
                    state = CppState.symbol
        elif state == CppState.line_comment:
            # Skip to the end of the line
            while len(s) > 0 and not endline.has(s[0]):
                s = s[1:]
            state = CppState.whitespace
        elif state == CppState.block_comment:
            # Skip to the "*/"
            while len(s) > 1 and ((not s[0] == '*') or (not s[1] == '/')):
                s = s[1:]
            s = s[2:] # Discard the "*/" or whatever two characters remain
            state = CppState.whitespace
        elif state == CppState.identifier:
            # Consume the token
            while len(s) > 0 and alpha_num.has(s[0]):
                tok += s[0]
                s = s[1:]

            # Identify the token
            if tok in built_in_tokens:
                output.append(f't{built_in_tokens[tok]}')
            else:
                output.append('t0')
            state = CppState.whitespace
        elif state == CppState.number:
            # Skip the number
            while len(s) > 0 and num.has(s[0]):
                tok += s[0]
                s = s[1:]

            # Identify the number
            if tok == '0':
                output.append('0')
            elif tok == '1':
                output.append('1')
            elif tok == '2':
                output.append('2')
            else:
                output.append('n')
            state = CppState.whitespace
        elif state == CppState.string:
            if len(s) > 0 and s[0] == '"':
                s = s[1:]
            escape = False
            while (len(s) > 0):
                if not escape and s[0] == '"':
                    break
                if endline.has(s[0]):
                    break
                escape = False
                if s[0] == '\\':
                    escape = True
                s = s[1:]
            if len(s) > 0:
                s = s[1:]
            output.append('s')
            state = CppState.whitespace
        else:
            assert state == CppState.symbol
            if len(s) > 0:
                output.append(s[0])
                s = s[1:]
            state = CppState.whitespace
    return ''.join(output)

def tokenize_cpp_file(s:str) -> str:
    return tokenize_cpp_like_file(s, built_in_cpp_tokens)

def tokenize_java_file(s:str) -> str:
    return tokenize_cpp_like_file(s, built_in_java_tokens)

def tokenize_javascript_file(s:str) -> str:
    return tokenize_cpp_like_file(s, built_in_javascript_tokens)

_built_in_py_tokens = [
    '__init__',
    '__file__',
    '__main__',
    '__name__',
    'and',
    'Any',
    'append',
    'as',
    'assert',
    'b',
    'break',
    'class',
    'close',
    'continue',
    'def',
    'del',
    'Dict',
    'in',
    'if',
    'import',
    'else',
    'elif',
    'except',
    'f',
    'False',
    'float',
    'for',
    'from',
    'global',
    'in',
    'int',
    'key',
    'lambda',
    'len',
    'List',
    'max',
    'min',
    'Mapping',
    'None',
    'not',
    'open',
    'Optional',
    'or',
    'os',
    'pop'
    'r',
    'raise',
    'range',
    'return',
    'self',
    'str',
    'sys',
    'traceback',
    'try',
    'True',
    'Tuple',
    'Union',
    'while',
    'with',
    'yield',
]
built_in_py_tokens = { v:(i+1) for i,v in enumerate(_built_in_py_tokens) }

class PyState(Enum):
    start_line = 1
    whitespace = 2
    comment = 3
    identifier = 4
    number = 5
    string = 6
    symbol = 7

def tokenize_python_file(s:str) -> str:
    # Make a bunch of useful character sets
    alpha = CharSet('A-Za-z_')
    alpha_num = CharSet('A-Za-z_0-9')
    num = CharSet('0-9')
    whitespace = CharSet(' \t')
    endline = CharSet('\r\n')
    quote = CharSet('\'"')

    # Tokenize the string
    output = []
    state = PyState.start_line
    tok = ''
    indent_spaces = 0
    stack:List[str] = []
    while len(s) > 0:
        if state == PyState.start_line:
            if len(stack) > 0:
                state = PyState.whitespace
            else:
                # Measure the indentation level
                while len(s) > 0 and endline.has(s[0]):
                    s = s[1:]
                indent = 0
                while len(s) > 0 and whitespace.has(s[0]):
                    indent += 1
                    s = s[1:]

            # See if the indentation level went up or down or stayed the same
            if len(s) > 0 and not endline.has(s[0]):
                if indent > indent_spaces:
                    indent_spaces = indent
                    output.append(f'u')
                elif indent < indent_spaces:
                    indent_spaces = indent
                    output.append(f'd')
                state = PyState.whitespace
        elif state == PyState.whitespace:
            # Skip whitespace
            while len(s) > 0 and whitespace.has(s[0]):
                s = s[1:]
            tok = ''
            if len(s) > 0:
                if endline.has(s[0]):
                    state = PyState.start_line
                    s = s[1:]
                elif s[0] == '#':
                    state = PyState.comment
                    s = s[1:]
                elif s[0] == '[':
                    output.append('[')
                    stack.append(']')
                    s = s[1:]
                elif s[0] == '{':
                    output.append('{')
                    stack.append('}')
                    s = s[1:]
                elif s[0] == '(':
                    output.append('(')
                    stack.append(')')
                    s = s[1:]
                elif s[0] == ']' or s[0] == '}' or s[0] == ')':
                    output.append(s[0])
                    while len(stack) > 0 and stack[-1] != s[0]:
                        stack.pop()
                    if len(stack) > 0 and stack[-1] == s[0]:
                        stack.pop()
                    s = s[1:]
                elif alpha.has(s[0]):
                    state = PyState.identifier
                elif num.has(s[0]):
                    state = PyState.number
                elif quote.has(s[0]):
                    state = PyState.string
                else:
                    state = PyState.symbol
        elif state == PyState.comment:
            # Skip to the end of the line
            while len(s) > 0 and not endline.has(s[0]):
                s = s[1:]
            state = PyState.start_line           
        elif state == PyState.identifier:
            # Consume the token
            while len(s) > 0 and alpha_num.has(s[0]):
                tok += s[0]
                s = s[1:]

            # Identify the token
            if tok in built_in_py_tokens:
                output.append(f't{built_in_py_tokens[tok]}')
            else:
                output.append('t0')
            state = PyState.whitespace
        elif state == PyState.number:
            # Skip the number
            while len(s) > 0 and num.has(s[0]):
                tok += s[0]
                s = s[1:]

            # Identify the number
            if tok == '0':
                output.append('0')
            elif tok == '1':
                output.append('1')
            elif tok == '2':
                output.append('2')
            else:
                output.append('n')
            state = PyState.whitespace
        elif state == PyState.string:
            endc = '\''
            if len(s) > 0 and s[0] == '"':
                s = s[1:]
                endc = '"'
            elif len(s) > 0 and s[0] == '\'':
                s = s[1:]
            escape = False
            while (len(s) > 0):
                if not escape and s[0] == endc:
                    break
                if endline.has(s[0]):
                    break
                escape = False
                if s[0] == '\\':
                    escape = True
                s = s[1:]
            if len(s) > 0:
                s = s[1:]
            output.append('s')
            state = PyState.whitespace
        else:
            assert state == PyState.symbol
            if len(s) > 0:
                output.append(s[0])
                s = s[1:]
            state = PyState.whitespace
    return ''.join(output)

ext_to_tokenizer = {
    '.py': tokenize_python_file,
    '.cpp': tokenize_cpp_file,
    '.hpp': tokenize_cpp_file,
    '.h': tokenize_cpp_file,
    '.c': tokenize_cpp_file,
    '.js': tokenize_javascript_file,
    '.java': tokenize_java_file,
    '.ts': tokenize_javascript_file,
}

skipped_extensions:Set[str] = set()

def tokenize_folder_tree(foldername:str) -> str:
    output:List[str] = []
    for path, folders, files in os.walk(foldername):
        for filename in files:
            if len(filename) < 1 or filename[0] == '.':
                continue
            _, ext = os.path.splitext(filename)
            if ext in ext_to_tokenizer:
                tokenizer = ext_to_tokenizer[ext]
                with open(os.path.join(path, filename), 'r') as f:
                    s = f.read()
                output.append(tokenizer(s))
            else:
                if not ext in skipped_extensions:
                    print(f'Skipping files with extension {ext}')
                    skipped_extensions.add(ext)
    return '                '.join(output)

def code_to_tok_set(s:str, tok_len:int) -> Set[str]:
    tok_set:Set[str] = set()
    for i in range(len(s) + 1 - tok_len):
        tok = s[i:i+tok_len]
        tok_set.add(tok)
    return tok_set

# Pass in a folder name.
# Tokenizes and compares each sub-folder.
# Returns a list of tuples sorted by suspiciousness.
# The first element of the tuple is the folder name of the plagiarizer.
# The second element of the tuple is the folder it appears to have plagiarized from.
# The third element indicates the suspiciousness,
# which is computed as the percentage of tokens from the first folder that are also contained in the second folder,
# weighted by the rarity of the token across all folders.
def most_suspicious_submissions(base_folder:str, tok_len:int=16) -> List[Tuple[str, str, float]]:
    folders = [ os.path.join(base_folder, f) for f in os.listdir(base_folder) if not os.path.isfile(os.path.join(base_folder, f)) ]
    print(f'folders={folders}')

    # Count the frequency of every token
    print(f'Tokenizing {len(folders)} submissions...')
    tok_count:Dict[str,int] = {}
    code:List[Tuple[str,str]] = []
    for folder in folders:
        s = tokenize_folder_tree(folder)
        code.append((folder, s))
        tok_set = code_to_tok_set(s, tok_len)
        for tok in tok_set:
            if tok in tok_count:
                tok_count[tok] += 1
            else:
                tok_count[tok] = 1

    # Assess the percentage contained between each pair of folders
    total_pairs = (len(folders) ** 2 - len(folders)) // 2
    i = 0
    suspect_list:List[Tuple[str,str,float]] = []
    for index_a in range(len(code)):
        set_a = code_to_tok_set(code[index_a][1], tok_len)
        if len(set_a) == 0:
            #print(f'{code[index_a][0]} contains no tokens')
            i += ((len(code) - 1) - index_a)
            continue
        for index_b in range(index_a + 1, len(code)):
            set_b = code_to_tok_set(code[index_b][1], tok_len)
            if len(set_b) == 0:
                #print(f'{code[index_b][0]} contains no tokens')
                i += 1
                continue
            i += 1

            # Compute the portion of a in b
            sum_rarity = 0
            sum_suspiciousness = 0
            for tok in set_a:
                rarity = len(code) - tok_count[tok]
                if tok in set_b:
                    sum_suspiciousness += rarity
                sum_rarity += rarity
            suspect_list.append((code[index_a][0], code[index_b][0], sum_suspiciousness / sum_rarity))

            # Compute the portion of b in a
            sum_rarity = 0
            sum_suspiciousness = 0
            for tok in set_b:
                rarity = len(code) - tok_count[tok]
                if tok in set_a:
                    sum_suspiciousness += rarity
                sum_rarity += rarity
            suspect_list.append((code[index_b][0], code[index_a][0], sum_suspiciousness / sum_rarity))

            print(f'Compared {i}/{total_pairs} pairs of folders')
    
    # Sort by suspiciousness
    print()
    suspect_list.sort(key=lambda x:-x[2])
    return suspect_list

if __name__ == '__main__':
    suspects = most_suspicious_submissions('/home/mike/box/uark/paradigms/projects')
    for i in range(len(suspects)):
        sus = suspects[i]
        print(f'{sus[2]*100:.2f}% of {os.path.basename(sus[0])} is in {os.path.basename(sus[1])}')
