
# parsetab_expression.py
# This file is automatically generated. Do not edit.
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'leftMODleftPLUSMINUSleftTIMESDIVIDErightUMINUSrightPOWleftGTGTELTLTEEQNEQNAME INT FLOAT POW MOD GT GTE LT LTE EQ NEQ PLUS MINUS TIMES DIVIDE EQUALS LPAREN RPAREN COMMA RBRACK LBRACK RBRACE LBRACE COLON STRINGstatement : expressionexpression : expression PLUS expression\n                      | expression MINUS expression\n                      | expression TIMES expression\n                      | expression DIVIDE expression\n                      | expression POW expression\n                      | expression MOD expression\n                      | expression GT expression\n                      | expression GTE expression\n                      | expression LT expression\n                      | expression LTE expression\n                      | expression EQ expression\n                      | expression NEQ expressionexpression : MINUS expression %prec UMINUSexpression : FLOAT NAME\n                      | INT NAMEexpression : FLOAT\n                      | INTexpression : STRINGexpression : NAME LPAREN arglist RPAREN\n                      | NAME LPAREN kwarglist RPAREN\n                      | NAME LPAREN arglist COMMA kwarglist RPARENexpression : NAMEexpression : NAME NAMEarglist : expression\n                   | arglist COMMA expressionkwarglist : NAME EQUALS expression\n                     | kwarglist COMMA NAME EQUALS expressionexpression : LBRACK listentry RBRACKexpression : LBRACE dictentry RBRACElistentry : expression\n                     | listentry COMMA expressiondictentry : expression COLON expression\n                     | dictentry COMMA expression COLON expressionexpression : LPAREN expression RPAREN'
    
_lr_action_items = {'DIVIDE':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[11,-17,-18,-23,-19,11,11,-14,-15,11,-16,-24,-5,-9,-4,11,-8,-11,-6,-13,-10,11,11,-12,-29,-30,-35,11,-23,11,11,11,-20,-21,11,11,11,-22,11,]),'RPAREN':([6,8,9,10,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,52,53,54,58,60,64,65,67,69,71,],[-17,-18,-23,-19,-14,-15,50,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,-25,58,60,-23,-20,-21,-26,69,-27,-22,-28,]),'TIMES':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[13,-17,-18,-23,-19,13,13,-14,-15,13,-16,-24,-5,-9,-4,13,-8,-11,-6,-13,-10,13,13,-12,-29,-30,-35,13,-23,13,13,13,-20,-21,13,13,13,-22,13,]),'PLUS':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[14,-17,-18,-23,-19,14,14,-14,-15,14,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,14,-3,-12,-29,-30,-35,14,-23,14,14,14,-20,-21,14,14,14,-22,14,]),'GT':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[15,-17,-18,-23,-19,15,15,15,-15,15,-16,-24,15,-9,15,15,-8,-11,15,-13,-10,15,15,-12,-29,-30,-35,15,-23,15,15,15,-20,-21,15,15,15,-22,15,]),'RBRACE':([6,8,9,10,26,27,28,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,56,58,60,68,69,],[-17,-18,-23,-19,49,-14,-15,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,-33,-20,-21,-34,-22,]),'POW':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[17,-17,-18,-23,-19,17,17,17,-15,17,-16,-24,17,-9,17,17,-8,-11,17,-13,-10,17,17,-12,-29,-30,-35,17,-23,17,17,17,-20,-21,17,17,17,-22,17,]),'LTE':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[16,-17,-18,-23,-19,16,16,16,-15,16,-16,-24,16,-9,16,16,-8,-11,16,-13,-10,16,16,-12,-29,-30,-35,16,-23,16,16,16,-20,-21,16,16,16,-22,16,]),'LBRACE':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,]),'INT':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,]),'COLON':([6,8,9,10,25,27,28,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,57,58,60,69,],[-17,-18,-23,-19,47,-14,-15,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,63,-20,-21,-22,]),'MINUS':([0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,54,55,56,57,58,59,60,62,63,64,67,68,69,70,71,],[5,21,5,5,5,-17,5,-18,-23,-19,5,5,5,5,5,5,5,5,5,5,5,5,21,21,-14,-15,21,-16,5,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,21,-3,-12,5,-29,5,5,-30,-35,21,-23,21,21,21,-20,5,-21,5,5,21,21,21,-22,5,21,]),'$end':([1,4,6,8,9,10,27,28,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,58,60,69,],[-1,0,-17,-18,-23,-19,-14,-15,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,-20,-21,-22,]),'MOD':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[20,-17,-18,-23,-19,20,20,-14,-15,20,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,20,-23,20,20,20,-20,-21,20,20,20,-22,20,]),'FLOAT':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,]),'GTE':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[12,-17,-18,-23,-19,12,12,12,-15,12,-16,-24,12,-9,12,12,-8,-11,12,-13,-10,12,12,-12,-29,-30,-35,12,-23,12,12,12,-20,-21,12,12,12,-22,12,]),'LT':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[19,-17,-18,-23,-19,19,19,19,-15,19,-16,-24,19,-9,19,19,-8,-11,19,-13,-10,19,19,-12,-29,-30,-35,19,-23,19,19,19,-20,-21,19,19,19,-22,19,]),'LPAREN':([0,2,3,5,7,9,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,54,59,62,63,70,],[7,7,7,7,7,31,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,31,7,7,7,7,]),'RBRACK':([6,8,9,10,23,24,27,28,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,55,58,60,69,],[-17,-18,-23,-19,46,-31,-14,-15,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,-32,-20,-21,-22,]),'LBRACK':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,]),'EQUALS':([54,66,],[62,70,]),'COMMA':([6,8,9,10,23,24,26,27,28,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,52,53,54,55,56,58,60,64,65,67,68,69,71,],[-17,-18,-23,-19,45,-31,48,-14,-15,-16,-24,-5,-9,-4,-2,-8,-11,-6,-13,-10,-7,-3,-12,-29,-30,-35,-25,59,61,-23,-32,-33,-20,-21,-26,61,-27,-34,-22,-28,]),'NEQ':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[18,-17,-18,-23,-19,18,18,18,-15,18,-16,-24,18,-9,18,18,-8,-11,18,-13,-10,18,18,-12,-29,-30,-35,18,-23,18,18,18,-20,-21,18,18,18,-22,18,]),'NAME':([0,2,3,5,6,7,8,9,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,54,59,61,62,63,70,],[9,9,9,9,28,9,30,32,9,9,9,9,9,9,9,9,9,9,9,9,54,9,9,9,32,54,66,9,9,9,]),'EQ':([1,6,8,9,10,24,25,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,49,50,51,54,55,56,57,58,60,64,67,68,69,71,],[22,-17,-18,-23,-19,22,22,22,-15,22,-16,-24,22,-9,22,22,-8,-11,22,-13,-10,22,22,-12,-29,-30,-35,22,-23,22,22,22,-20,-21,22,22,22,-22,22,]),'STRING':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'kwarglist':([31,59,],[53,65,]),'arglist':([31,],[52,]),'statement':([0,],[4,]),'listentry':([2,],[23,]),'expression':([0,2,3,5,7,11,12,13,14,15,16,17,18,19,20,21,22,31,45,47,48,59,62,63,70,],[1,24,25,27,29,33,34,35,36,37,38,39,40,41,42,43,44,51,55,56,57,64,67,68,71,]),'dictentry':([3,],[26,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> statement","S'",1,None,None,None),
  ('statement -> expression','statement',1,'p_statement_expr','Expression.py',150),
  ('expression -> expression PLUS expression','expression',3,'p_expression_binop','Expression.py',155),
  ('expression -> expression MINUS expression','expression',3,'p_expression_binop','Expression.py',156),
  ('expression -> expression TIMES expression','expression',3,'p_expression_binop','Expression.py',157),
  ('expression -> expression DIVIDE expression','expression',3,'p_expression_binop','Expression.py',158),
  ('expression -> expression POW expression','expression',3,'p_expression_binop','Expression.py',159),
  ('expression -> expression MOD expression','expression',3,'p_expression_binop','Expression.py',160),
  ('expression -> expression GT expression','expression',3,'p_expression_binop','Expression.py',161),
  ('expression -> expression GTE expression','expression',3,'p_expression_binop','Expression.py',162),
  ('expression -> expression LT expression','expression',3,'p_expression_binop','Expression.py',163),
  ('expression -> expression LTE expression','expression',3,'p_expression_binop','Expression.py',164),
  ('expression -> expression EQ expression','expression',3,'p_expression_binop','Expression.py',165),
  ('expression -> expression NEQ expression','expression',3,'p_expression_binop','Expression.py',166),
  ('expression -> MINUS expression','expression',2,'p_expression_uminus','Expression.py',181),
  ('expression -> FLOAT NAME','expression',2,'p_expression_mag','Expression.py',185),
  ('expression -> INT NAME','expression',2,'p_expression_mag','Expression.py',186),
  ('expression -> FLOAT','expression',1,'p_expression_number','Expression.py',190),
  ('expression -> INT','expression',1,'p_expression_number','Expression.py',191),
  ('expression -> STRING','expression',1,'p_expression_string','Expression.py',195),
  ('expression -> NAME LPAREN arglist RPAREN','expression',4,'p_expression_func','Expression.py',199),
  ('expression -> NAME LPAREN kwarglist RPAREN','expression',4,'p_expression_func','Expression.py',200),
  ('expression -> NAME LPAREN arglist COMMA kwarglist RPAREN','expression',6,'p_expression_func','Expression.py',201),
  ('expression -> NAME','expression',1,'p_expression_name','Expression.py',232),
  ('expression -> NAME NAME','expression',2,'p_expression_namewunit','Expression.py',238),
  ('arglist -> expression','arglist',1,'p_arglist','Expression.py',251),
  ('arglist -> arglist COMMA expression','arglist',3,'p_arglist','Expression.py',252),
  ('kwarglist -> NAME EQUALS expression','kwarglist',3,'p_kwarglist','Expression.py',259),
  ('kwarglist -> kwarglist COMMA NAME EQUALS expression','kwarglist',5,'p_kwarglist','Expression.py',260),
  ('expression -> LBRACK listentry RBRACK','expression',3,'p_expression_list','Expression.py',268),
  ('expression -> LBRACE dictentry RBRACE','expression',3,'p_expression_dict','Expression.py',272),
  ('listentry -> expression','listentry',1,'p_listentry','Expression.py',276),
  ('listentry -> listentry COMMA expression','listentry',3,'p_listentry','Expression.py',277),
  ('dictentry -> expression COLON expression','dictentry',3,'p_dictentry','Expression.py',284),
  ('dictentry -> dictentry COMMA expression COLON expression','dictentry',5,'p_dictentry','Expression.py',285),
  ('expression -> LPAREN expression RPAREN','expression',3,'p_expression_group','Expression.py',293),
]
