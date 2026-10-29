# Dumbo storefront vs Jumbo: structural comparison

Date: 2026-10-28. Method: Playwright with Chrome headless, viewport 1366×1000, one load per site,
DOM metrics only. Screenshots were written to the OS temp directory and are not versioned.

The goal is structural and interaction parity with a real supermarket storefront, not a pixel copy:
Dumbo uses its own name, copy, palette (teal/mango/coral) and original SVG category icons. No Jumbo
text, logo, image or asset is reused.

## Metrics

| Metric | Dumbo | Jumbo |
|---|---:|---:|
| Header links | 13 | 55 |
| Navigation links | 10 | 34 |
| Product cards | 50 | n/a (different class names; 42 "Agregar" buttons) |
| "Agregar" buttons | 50 | 42 |
| Inputs | 2 | 10 |
| Buttons | 53 | 74 |
| Footer links | 10 | 49 |
| Images | 50 | 127 |
| Sections | 7 | 28 |
| Page height (px) | 5,695 | 12,197 |
| Cookie banner | yes | yes |
| Search box | yes | yes |

## What matches

- Top strip, sticky header with logo, search, account and cart, category navigation, hero, category
  chips, offers, best sellers, new arrivals, a full catalog and a multi-column footer.
- Cookie banner with a configuration link and a "necessary only" action; optional categories off by
  default.
- Product cards with brand, name, unit, current and previous price, discount badge and add button.
- Responsive layout: four columns on desktop, two on small screens, horizontal scrolling for offers.

## Differences and why

- **Content volume.** Jumbo has many promotional strips and 28 sections; Dumbo has 7. The target is
  an MVP with a 32-product, 8-category seed and 6 offers, enough to exercise the privacy surfaces.
- **Assets.** Dumbo uses original line-art icons per category on a color field. Copying product
  photography, the logo or the site text is a trademark/copyright risk and was ruled out in L15.
- **Links.** Dumbo exposes only routes that exist (account, orders, rights, privacy, cookies); Jumbo
  has dozens of marketing and help links. Dead links were preferred not to be added.
- **Inputs.** Dumbo uses plain server-rendered forms (2 inputs on the home page); Jumbo uses a
  JavaScript-heavy storefront with more controls.

## Refinements applied to the target

- Seed expanded from 8 to 32 products across 8 categories, with units, previous prices and badges.
- Offers get their own filter (`/?ofertas=1`), horizontal carousel and discount percentages.
- Hero, benefits strip, category chips, new-arrivals section, richer footer and responsive CSS.
- Original SVG icons for the eight categories, so cards no longer show empty blocks.

## Conclusion

The storefront now has the same information architecture and component set as the reference, with a
different brand and palette. The remaining gap is promotional volume and photography, neither of
which changes the privacy surfaces the experiment measures.
