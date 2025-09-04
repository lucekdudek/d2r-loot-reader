# Notes

## Todo

- item_parser.py unit tests
- `"+# to [Skill]"` affix is getting mixed with `"+# to Strength"`

## Output schema

```json
{
  "quality": "Runeword | Unique | Set | Rare | Magic | Base",
  "name": "string",
  "base": "string",
  "slot": "string",
  "tier": "string", // e.g. "Normal", "Exceptional", "Elite"
  "requirements": {
    "strength": "int",
    "dexterity": "int",
    "level": "int",
    "class": "string"
  },
  "stats": {
    "1h_damage": [min, max],
    "2h_damage": [min, max],
    "defense": "int"
  },
  "affixes": {
    "string": ["int", "..."] // "Adds #-# Lightning Damage": [1, 8]
    // ...more affixes
  },
  "tooltip": [
    "string"
    // ...lines as seen in-game
  ]
}
```
