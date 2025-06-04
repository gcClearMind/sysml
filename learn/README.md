## getJson_Road.py 

用于从知识图谱中得到两个标签之间的相关路径以及对应的规则

##### 输入

知识图谱数据库、两个标签名以及路径最大长度

##### 输出

json格式的规则以及对应的路径，输出在data/path中

## AnyBURL

相关文件为AnyBURL-23-1.jar、config-learn.properties

启动的流程见https://web.informatik.uni-mannheim.de/AnyBURL/#:~:text=AnyBURL%20,Link%20to%20paper%20published

##### 输入

需要有一个train.txt文件，表示需要推理的三元组

##### 输出

rules-10、rules-50、rules-100；分别表示10s、50s、100s下的推理结果。

推理结果的每一列分别表示、满足头部的路径数、满足全部条件的路径数、置信度、规则

## getTriples.py

用以从知识图谱中得到三元组的代码

##### 输入

知识图谱数据库，注意query语句

##### 输出

triples_with_all.txt表示全部的三元组;triples_with_local表示优化后的三元组。

## sorted.py

用以对推理出来的结果进行筛选排序

##### 输入

rules-10/50/100

##### 输出

sorted_rules.txt