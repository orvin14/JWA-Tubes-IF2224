class Node:
    def __init__(self, name, token=None):
        self.name = name
        self.children = []
        self.token = token

    def add_child(self, node):
        if node:
            self.children.append(node)

    def print_tree(self, level=0):
        if level == 0:
            indent = ""
            prefix = ""
        else:
            indent = "   " * (level - 1)
            prefix = "└─ "
        if self.token:
            token_type, token_value = self.token[0], self.token[1]
            print(f"{indent}{prefix}{token_type}({token_value!r})")
        else:
            print(f"{indent}{prefix}<{self.name}>")
        for child in self.children:
            child.print_tree(level + 1)