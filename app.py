import functools, re
import graphviz as gv

class LSAlgo:
    RE_STRT_OPER = r'[YA]([0]|[n])'
    RE_END_OPER = r'[YA][k]'
    RE_OPER = r'[YA]\d+'
    RE_LGC_CNDTN = r'[x]\d+'
    RE_CNDTN_JMP = r'[<>]\d+'
    RE_NON_CNDTN_JMP = r'w'

    RE_CNDTN_DWN_JMP = '<'
    RE_CNDTN_UP_JMP = '>'

    REX_TOKENS = [r'[YA]([0]|[n])', r'[YA][k]', r'[YA]\d+', r'[x]\d+', r'[<>]\d+', r'w']

    def __init__(self, string_expr):
        self.string_expr = string_expr
        self.tokens = []
        self.eval_dict = []
        self.filename = 'img/g'

    def read_string(self):
        if self.string_expr:
            self.tokens = str(self.string_expr).split(' ')

    def parse_string(self):
        for index, token in enumerate(self.tokens):
            if re.match(self.RE_STRT_OPER, token) and index == 0:
                self.eval_dict.append({
                    'type': 'RE_STRT_OPER',
                    'index': index,
                    'label': token
                })
            elif (re.match(self.RE_STRT_OPER, token) and index != 0) or \
                    (re.match(self.RE_STRT_OPER, token) is None and index == 0):
                raise Exception("Missing start point! Y0 isnt on 1 position! Pos {0}.".format(index+1))
            if re.match(self.RE_END_OPER, token) and index == len(self.tokens) - 1:
                self.eval_dict.append({
                    'type': 'RE_END_OPER',
                    'index': index,
                    'label': token
                })
            elif (re.match(self.RE_END_OPER, token) and index != len(self.tokens) - 1) or \
                    (re.match(self.RE_END_OPER, token) is None and index == len(self.tokens) - 1):
                raise Exception("Missing start point! Yk isnt on last position! Pos {0}.".format(index+1))
            if re.match(self.RE_OPER, token):
                cs = re.search(r'\d+', token)
                code_number = int(cs.group(0))
                if code_number != 0:
                    self.eval_dict.append({
                        'type': 'RE_OPER',
                        'index': index,
                        'code_number': code_number,
                        'label': token
                    })
            if re.match(self.RE_LGC_CNDTN, token):
                cs = re.search(r'\d+', token)
                code_number = int(cs.group(0))
                self.eval_dict.append({
                    'type': 'RE_LGC_CNDTN',
                    'index': index,
                    'code_number': code_number,
                    'label': token
                })
            if re.match(self.RE_CNDTN_UP_JMP, token):
                cs = re.search(r'\d+', token)
                code_number_up = int(cs.group(0))
                index_down = None
                if str(self.RE_CNDTN_DWN_JMP + str(code_number_up)) in self.tokens:
                    index_down = self.tokens.index(str(self.RE_CNDTN_DWN_JMP + str(code_number_up)))
                else:
                    raise Exception("No end point for JMP! Pos {0}.".format(index+1))
                if re.match(self.RE_LGC_CNDTN, self.tokens[index - 1]) or \
                    re.match(self.RE_NON_CNDTN_JMP, self.tokens[index - 1]) and index_down is not None:
                    self.eval_dict.append({
                        'type': 'RE_CNDTN_UP_JMP',
                        'from_index': index,
                        'code_number': code_number_up,
                        'to_index': index_down
                    })
            if re.match(self.RE_CNDTN_DWN_JMP, token):
                cs = re.search(r'\d+', token)
                code_number_up = int(cs.group(0))
                if self.tokens.count(str(self.RE_CNDTN_DWN_JMP + str(code_number_up))) > 1:
                    raise Exception("There're too many down JMPS! Pos {0}.".format(index+1))


    def prepare_tree_gsa(self):
        node_list = []
        for item in self.eval_dict:
            if item['type'] is 'RE_STRT_OPER' or item['type'] is 'RE_END_OPER':
                node_list.append((item['label'], {'label': item['label'], 'shape': 'ellipse'}))
            elif item['type'] is 'RE_OPER':
                node_list.append((item['label'], {'label': item['label'], 'shape': 'box'}))
            elif item['type'] is 'RE_LGC_CNDTN':
                node_list.append((item['label'], {'label': item['label'], 'shape': 'diamond', 'tailport': 'w', 'headport': 'n'}))
        links_list = []
        for index, item in enumerate(self.eval_dict):
            if item['type'] in ['RE_STRT_OPER', 'RE_OPER']:
                if self.eval_dict[index+1]['type'] in ['RE_STRT_OPER', 'RE_OPER', 'RE_END_OPER', 'RE_LGC_CNDTN']:
                    links_list.append((item['label'], self.eval_dict[index+1]['label']))
                elif self.eval_dict[index+1]['type'] is 'RE_CNDTN_UP_JMP':
                    jmp_to_index = self.eval_dict[index + 1]['to_index'] + 1
                    index_t0 = 0
                    while True:
                        if self.eval_dict[index_t0]['type'] in ['RE_STRT_OPER', 'RE_OPER', 'RE_END_OPER',
                                                                'RE_LGC_CNDTN'] and \
                                        self.eval_dict[index_t0]['index'] is jmp_to_index:
                            links_list.append(((item['label'], self.eval_dict[index_t0]['label'])))
                            break
                        index_t0 += 1
                        if index_t0 == len(self.eval_dict):
                            index_t0 = 0
                            jmp_to_index += 1
                        if jmp_to_index == len(self.tokens):
                            raise Exception(
                                "Cant find link! Parse error! Item {0} Pos {1}.".format(item['label'], item['index']))
            elif item['type'] is 'RE_LGC_CNDTN':
                if self.eval_dict[index+1]['type'] is 'RE_CNDTN_UP_JMP':
                    jmp_to_index = self.eval_dict[index + 1]['to_index'] + 1
                    # jmp_cndtn_0 = False
                    index_t0, index_t1 = 0, index + 2
                    while True:
                        if self.eval_dict[index_t0]['type'] in ['RE_STRT_OPER', 'RE_OPER', 'RE_END_OPER', 'RE_LGC_CNDTN'] and \
                                self.eval_dict[index_t0]['index'] is jmp_to_index:
                            links_list.append(((item['label'], self.eval_dict[index_t0]['label']), {'label': 'false'}))
                            break
                        index_t0 += 1
                        if index_t0 == len(self.eval_dict):
                            index_t0 = 0
                            jmp_to_index += 1
                        if jmp_to_index == len(self.tokens):
                            raise Exception("Cant find link! Parse error! Item {0} Pos {1}.".format(item['label'], item['index']))
                            # break
                    while True:
                        if self.eval_dict[index_t1]['type'] in ['RE_STRT_OPER', 'RE_OPER', 'RE_END_OPER', 'RE_LGC_CNDTN']:
                            links_list.append(((item['label'], self.eval_dict[index_t1]['label']), {'label': 'true'}))
                            break
                        index_t1 += 1
                        if index_t0 == len(self.eval_dict):
                            raise Exception("Cant find link! Parse error! Item {0} Pos {1}. (Possible missing end operator Yk)".format(item['label'], item['index']))
                            # break
        return node_list, links_list


    def draw(self):
        graph = gv.Digraph(format='svg')
        nodes, links = self.prepare_tree_gsa()
        try:
            for node in nodes:
                if isinstance(node, tuple):
                    graph.node(node[0], **node[1])
                else:
                    graph.node(node)
            for edge in links:
                if isinstance(edge[0], tuple):
                    graph.edge(*edge[0], **edge[1])
                else:
                    graph.edge(*edge)
            graph.render(filename=self.filename)
        except Exception:
            pass


if __name__ == '__main__':
    test = 'Yn <5 Y1 x1 >1 x2 >2 <4 Y3 x3 >5 Y4 w >3 <1 Y2 w >4 <2 Y5 <3 Yk'
    l = LSAlgo(test)
    l.read_string()
    l.parse_string()
    l.prepare_tree_gsa()
    l.draw()
    pass