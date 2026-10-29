# Dumbo storefront vs Jumbo: structural comparison

Date: 2026-10-28. Method: Playwright with Chrome headless, viewport 1366×1000, DOM metrics only.
Screenshots were written to the OS temp directory and are not versioned.

Dumbo uses its own name, copy, palette (teal/mango/coral) and generated SVG product images. No
Jumbo text, logo, image or asset is reused. The goal is structural and interaction parity, not a
pixel copy.

## Metrics

| Metric | Dumbo home | Dumbo catalog | Dumbo product | Jumbo home |
|---|---:|---:|---:|---:|
| Header links | 26 | 26 | 26 | 55 |
| Navigation links | 23 | 25 | 25 | 34 |
| Product cards | 60 | 24 | 3 | n/a (42 add buttons) |
| "Agregar" buttons | 60 | 24 | 4 | 42 |
| Inputs | 1 | 3 | 2 | 10 |
| Buttons | 62 | 27 | 6 | 74 |
| Footer links | 18 | 18 | 18 | 49 |
| Product graphics | 60 inline | 24 inline | 5 inline | 127 `<img>` |
| Sections | 17 | 0 | 2 | 28 |
| Page height (px) | 7,525 | 2,948 | 1,542 | 12,197 |
| Cookie banner | yes | yes | yes | yes |
| Search box | yes | yes | yes | yes |

## What matches

- Top strip, sticky header with logo, search, account and cart, category navigation, hero, category
  chips, offers, best sellers, new arrivals, eight category showcases, a promo band, brands and a
  five-column footer.
- Cookie banner with a configuration link and a "necessary only" action; optional categories off by
  default.
- A full catalog with search, category filter, "only offers" filter and pagination; 152 products in
  20 categories.
- Product detail pages with description, unit, stock, current and previous price, related products
  and an add-to-cart form.
- Product cards with image, brand, name, unit, prices and a discount badge. Images are generated
  SVGs per product (`/img/{id}.svg`), not copied photography.
- Responsive layout: four columns on desktop, two on small screens, horizontal scrolling for offers.

## Differences and why

- **Content volume.** Jumbo has 28 sections and 127 images; Dumbo's home has 17 sections and 60
  inline illustrations. The target is an MVP-sized storefront, not a full commercial site.
- **Assets.** Dumbo draws category illustrations inline (SVG paths in the document) so the art does
  not depend on image loading, caching or SVG support in the browser. Copying product photography,
  the logo or the site text is a trademark/copyright risk and was ruled out in L15.
- **Links.** Dumbo exposes only routes that exist; Jumbo has dozens of marketing and help links.
  Dead links were deliberately not added.
- **Forms.** Dumbo uses server-rendered forms (1 input on the home, 3 on the catalog); Jumbo is a
  JavaScript-heavy storefront with more controls.

## Refinements applied to the target

- Catalog expanded from 8 to 152 products across 20 categories, with category-appropriate units,
  previous prices and generated descriptions.
- Separate home, catalog (filters + pagination) and product detail routes.
- Offers carousel and `/catalog?ofertas=1`, best sellers, new arrivals, eight showcases, promo band,
  brand strip and category links in the footer.
- Generated per-product SVG images, original category line icons and a responsive stylesheet.

## Conclusion

The storefront now has the same information architecture and component set as the reference, with a
different brand and palette and more than enough catalog to exercise the privacy surfaces. The
remaining gap is promotional volume and professional photography, neither of which changes what the
experiment measures.
