def extract_handlers(server):
    for it in server._state.generic_handlers[0]._method_handlers.values():
        yield it.unary_unary.__name__
