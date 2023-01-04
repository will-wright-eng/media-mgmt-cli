## release process

1. upversion string in `setup.py` file

```python
VERSION = "0.3.0"
```

2. tag branch

```bash
git tag -a v0.2.0 -m "description of release"
```

3. git add/commit/push
4. merge pull request once tests pass
5. create new release (consistent with `git tag`)
