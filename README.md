# PennyFinder: Home Depot penny and clearance finder for Fresno, Clovis, Madera and Selma

An iPhone-installable web app (PWA). It has three tabs:
* **Clearance**: tracked clearance items at the 6 local stores. Shows % off, was price, clearance price, units in stock and when the store was last checked. The minimum-% slider defaults to 50%, and you can sort by % off, price, newest check, units or store.
* **Penny leads**: items shoppers have reported ringing up at $0.01 (Penny Recon's public list), with SKU, Internet #, UPC, CA report count and last report time. Any $0.01 item that appears in the local stock data is pinned at the top.
* **My finds**: add your own finds (with aisle/bay), import a CSV or JSON penny list, and export to CSV.

Stores: #663 Fresno, #1014 N Fresno, #1086 South Fresno, #664 Clovis, #1088 Madera, #8529 Selma.

## Where the data comes from
| Data | Source | How fresh |
|---|---|---|
| Per-store clearance price, was price, % off, units | spottedflips.com public city pages (`/clearance/home-depot/ca/<city>`) | Spotted rechecks each store about once a day. It covers roughly 1,000 tracked products, not every yellow tag. |
| Penny ($0.01) leads | pennyrecon.com `/data/items.json` (public JSON linked in its footer) | Updated daily. National, with state-level counts only. |
| City-level penny reports | pennycentral.com | **Link only.** Its terms forbid scraping. |
| homedepot.com | not used | Akamai returns 403 to cloud and datacenter IPs. We do not try to get around that. |

## Deploy (free, about 15 minutes, one GitHub account)
1. Create a free account at https://github.com/signup.
2. Create a new **public** repository named `pennyfinder`. GitHub Pages is free for public repos.
3. Upload these files, keeping the folders: `docs/`, `scripts/`, `.github/workflows/refresh.yml`, `requirements.txt`, `serve_local.py`, `README.md`.
   (The web uploader can skip the hidden `.github` folder. If it does, use **Add file → Create new file**, type `.github/workflows/refresh.yml` as the name, and paste the file's contents.)
4. Go to **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**. Save.
5. Go to **Settings → Pages → Build and deployment**. Set Source to "Deploy from a branch", Branch to `main`, folder `/docs`. Save.
6. Go to the **Actions** tab, open **refresh**, and tap **Run workflow** once. After that it runs every 3 hours on its own.
7. On the iPhone, open `https://<your-username>.github.io/pennyfinder/` in **Safari**, then tap **Share → Add to Home Screen**.
8. (Optional) Make Refresh start a run right away. Create a token at GitHub **Settings → Developer settings → Fine-grained tokens**: Repository access = only `pennyfinder`, Permissions → **Actions: Read and write**. Paste it, your username and the repo name into the app's **Setup** tab. Refresh will then start a run and show the new data in about 1–3 minutes. Without a token, Refresh loads the newest file, which is at most about 3 hours old.

## Run on a PC instead, with live refresh and no account
```
pip install beautifulsoup4
python serve_local.py        # then open http://localhost:8765
```
A phone on the same Wi-Fi can open `http://<PC-IP>:8765`. Refresh then runs the scraper immediately.

## Rules of the road
Penny prices are an internal "pull this item" signal. Home Depot does not officially sell penny items, and a store can refuse the sale. Leads are hints only: scan the item's own UPC at self-checkout. The refresh makes 5 polite page requests per run. Please don't raise the frequency much.
