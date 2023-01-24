# release notes

## process

1. upversion string in `setup.py` file using symantic versioning (major, minor, patch)

```python
VERSION = "0.1.0"
```

2. tag branch

```bash
git tag -a v0.1.0 -m "description of release"
git push origin v0.1.0
```

3. [local] git add/commit/push
4. [GitHub] merge pull request once tests pass
5. [GitHub] create new release
