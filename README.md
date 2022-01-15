# Musescore Sheet Music Download Tool

This is a tool for scraping sheet music from [musescore.com](https://musescore.com).

## Installation

Installation with pip is as simple as this:
```
pip install musescore
```

## Example

```python
import musescore

user  = 2170606
score = 5044504
dpi   = 40

musescore.download(user = user, score = score, dpi = dpi)
```
