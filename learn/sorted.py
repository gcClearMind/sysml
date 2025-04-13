import pandas as pd

# 文件路径（替换成你的文件路径）
input_file = 'rules-100'
output_file = 'sorted_rules.txt'

# 读取制表符分隔的文件
df = pd.read_csv(input_file, sep='\t', header=None)

# 可选：添加列名，便于理解
df.columns = ['Field1', 'Field2', 'Score', 'Rule']

# 将第 3 列 'Score' 转为数值类型
df['Score'] = pd.to_numeric(df['Score'], errors='coerce')

# df = df[df['Score'] != 1]

# 根据 'Score' 降序排序
df_sorted = df.sort_values(by='Score', ascending=False)

# 将结果输出为新的文件（仍然用 tab 分隔）
df_sorted.to_csv(output_file, sep='\t', header=False, index=False)

print(f'排序完成，结果已保存至 {output_file}')
