# Linksafe

Scan your repo for broken links. Whitelist links or files you wish to ignore. Works in private repos. Designed to be ideal for awesome-lists!  

## Example usage
```yaml
name: Link-check
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run linksafe
        uses: Yaraslaut/linksafe@main
        with: # comma seperated lists
          # use relative paths, if no dirs specified root dir is scanned
          ignored_links: "https://xyz.xyz"
          # use relative paths
          ignored_files: "./doc/HACKING.md"
          ignored_dirs: "_deps"
```

## Info
`.git` `build` `.cache` `.github` directories are automatically ignored. 
`https://example.com`,`http://localhost` and `http://unicode.org/emoji/charts/full-emoji-list.html` are automatically ignored.

All directories will be scanned, if you want to ommit some put them in `ignored_dirs` option.
