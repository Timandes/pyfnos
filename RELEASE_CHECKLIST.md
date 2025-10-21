# Fnos 发布准备清单

## 1. 项目结构
- [x] 项目名称已更改为 "fnos"
- [x] 包结构已正确配置 (fnos/ 包含 __init__.py 和 client.py)
- [x] pyproject.toml 配置正确
- [x] README.md 文档完整
- [x] LICENSE 文件已添加

## 2. 构建文件
- [x] fnos-0.1.0.tar.gz (源码分发包)
- [x] fnos-0.1.0-py3-none-any.whl (wheel包)

## 3. 发布前检查
- [x] 包可以成功构建
- [x] 包含所有必要的文件
- [x] 依赖关系正确声明
- [x] 元数据完整
- [x] 包可以成功导入和使用

## 4. 发布步骤

### 4.1. 测试安装 (可选)
```bash
pip install dist/fnos-0.1.0-py3-none-any.whl
```

### 4.2. 发布到PyPI
```bash
# 安装twine (如果尚未安装)
pip install twine

# 上传到PyPI (需要PyPI账户)
twine upload dist/*
```

### 4.3. 发布到TestPyPI (推荐先测试)
```bash
# 上传到TestPyPI
twine upload --repository testpypi dist/*

# 从TestPyPI安装测试
pip install --index-url https://test.pypi.org/simple/ fnos
```

## 5. 后续版本发布
1. 更新 `fnos/__init__.py` 中的版本号
2. 更新 `pyproject.toml` 中的版本号
3. 重新构建包: `python -m build`
4. 上传到PyPI: `twine upload dist/*`