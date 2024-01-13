class Parser:
    def __init__(self, data):
        assert type(data) == str
        self.data = data

    def match_consume(self, prefix):
        assert type(prefix) == str
        assert self.data.startswith(prefix)
        self.data = self.data[len(prefix):]

    def try_match_consume(self, prefix):
        assert type(prefix) == str
        if self.data.startswith(prefix):
            self.match_consume(prefix)
            return True
        else:
            return False

    def by_count(self, n):
        assert len(self.data) >= n
        out = self.data[:n]
        self.data = self.data[n:]
        return out

    def token_by_count(self, n):
        out = self.by_count(n)
        if len(self.data) > 0 and self.data[0] == '_':
            self.data = self.data[1:]
        return out

    def token(self):
        i = self.data.find('_')
        if i == -1:
            out = self.data
            self.data = ""
        else:
            out = self.data[:i]
            self.data = self.data[i+1:]
        return out

    def ident(self):
        n = int(self.token())
        return self.token_by_count(n)

    def match_consume_token(self, tok):
        out = self.try_match_consume_token(tok)
        if not out:
            raise Error("Bindgen: Parser: failed to match token {0}".format(tok))
        return out

    def try_match_consume_token(self, tok):
        assert type(tok) == str
        if self.data.startswith(tok):
            if len(self.data) == len(tok):
                self.data = ""
                return True
            if self.data[len(tok)] == '_':
                self.data = self.data[len(tok)+1:]
                return True
        return False

    def try_parse(self, lambda_fn):
        try:
            return lambda_fn(self)
        except:
            return False

    def ensure_empty(self):
        # For sequences, (strings, lists, tuples), use the fact that empty sequences are false.
        # Source: PEP 8, https://stackoverflow.com/questions/9573244/how-to-check-if-the-string-is-empty-in-python
        assert not self.data


def TInteger(parser):
    types = {
        "i8": "int8_t",
        "i16": "int16_t",
        "i32": "int32_t",
        "i64": "int64_t",
        "isize": "intptr_t",
        "u8": "uint8_t",
        "u16": "uint16_t",
        "u32": "uint32_t",
        "u64": "uint64_t",
        "usize": "size_t"
    }
    for k, v in types.items():
        out = parser.try_match_consume_token(k)
        if out:
            return v
    raise Error("Bindgen: Failed to parse TInteger")

def TPrimitive(parser):
    parser.match_consume_token("prim")
    out = parser.try_parse(TInteger)
    if out:
        return out
    if parser.try_match_consume_token("ptr"):
        return "const {0}*".format(TInteger(parser))
    if parser.try_match_consume_token("ptrmut"):
        return "{0}*".format(TInteger(parser))
    if parser.try_match_consume_token("string"):
        return "std::string"
    if parser.try_match_consume_token("unit"):
        return "void"
    raise Error("Bindgen: Failed to parse TPrimitive")

def TPair(parser):
    parser.match_consume_token("pair")
    ty1 = TBase(parser)
    ty2 = TBase(parser)
    return "std::pair<{0}, {1}>".format(ty1, ty2)

def TVec(parser):
    parser.match_consume_token("vec")
    ty = TBase(parser)
    return "std::vector<{0}>".format(ty)

def TBase(parser):
    for T in [TPrimitive, TPair, TVec]:
        out = parser.try_parse(T)
        if out:
            return out
    raise Error("Bindgen: Failed to parse TBase")

def TInput(parser):
    if parser.try_match_consume_token("bor"):
        return "const {0}&".format(TBase(parser))
    if parser.try_match_consume_token("bormut"):
        return "{0}&".format(TBase(parser))
    return TBase(parser)

def TOutput(parser):
    return TBase(parser)

def TArg(parser):
    name = parser.ident()
    ty = TBase(parser)
    return (name, ty)

def TFunction(parser):
    fn_name = parser.ident()
    num_args = int(parser.token())
    args = [TArg(parser) for _ in range(num_args)]
    out = TOutput(parser)
    return (fn_name, args, out)

def demangle(mangled):
    parser = Parser(mangled)
    if parser.try_match_consume("_basm_export_"):    
        bindgen_type = "export"
    elif parser.try_match_consume("_basm_import_"):
        bindgen_type = "import"
    else:
        raise Error("Bindgen: unknown bindgen type")
    out = TFunction(parser)
    parser.ensure_empty()
    return (bindgen_type, out)

if __name__ == '__main__':
    print(demangle("_basm_export_4_init_2_1_t_prim_i32_1_n_prim_i32_prim_unit"))
    print(demangle("_basm_export_4_game_0_prim_unit"))
    print(demangle("_basm_import_5_guess_1_1_b_prim_string_pair_prim_i32_prim_i32"))
    print(demangle("_basm_import_8_test_ptr_2_1_x_prim_ptr_usize_1_y_vec_pair_prim_i8_prim_u64_prim_ptrmut_u8"))