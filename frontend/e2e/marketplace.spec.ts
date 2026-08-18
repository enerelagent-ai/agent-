import { expect, test } from "@playwright/test";

test("sale and rent routes never mix transaction badges", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/sale$/);
  const saleCards = page.locator("article");
  await expect(saleCards.first()).toBeVisible();
  await expect(saleCards.locator("text=ТҮРЭЭСЛҮҮЛНЭ")).toHaveCount(0);
  await expect(saleCards.first().getByText("ЗАРНА", { exact: true })).toBeVisible();

  await page.goto("/rent");
  const rentCards = page.locator("article");
  await expect(rentCards.first()).toBeVisible();
  await expect(rentCards.locator("text=ЗАРНА")).toHaveCount(0);
  await expect(rentCards.first().getByText("ТҮРЭЭСЛҮҮЛНЭ", { exact: true })).toBeVisible();
});

test("district filter cannot return another district", async ({ page }) => {
  await page.goto("/sale");
  const districtSelect = page.getByLabel("Дүүрэг").first();
  const district = await districtSelect.locator("option").nth(1).getAttribute("value");
  expect(district).toBeTruthy();
  await districtSelect.selectOption(district as string);

  const responsePromise = page.waitForResponse(
    (response) => response.url().includes("/listings/search?") && response.ok(),
  );
  await page.getByRole("button", { name: "Хайх" }).first().click();
  await responsePromise;

  const cards = page.locator("article");
  await expect(cards.first()).toBeVisible();
  const cardCount = await cards.count();
  for (let index = 0; index < cardCount; index += 1) {
    await expect(cards.nth(index)).toContainText(district as string);
  }
});

test("listing card opens an internal detail page with source action", async ({ page }) => {
  await page.goto("/sale");
  const firstCardLink = page.locator("article a[href^='/listings/']").first();
  const detailPath = await firstCardLink.getAttribute("href");
  expect(detailPath).toMatch(/^\/listings\/\d+$/);
  await firstCardLink.click();

  await page.waitForURL(new RegExp(`${detailPath}$`), { timeout: 30_000 });
  await expect(page.locator("h1")).toBeVisible();
  await expect(page.getByRole("link", { name: /Эх зар дээр харах/ })).toBeVisible();
});

test("cursor next page has no cards from the first page", async ({ page }) => {
  await page.goto("/sale");
  const cardLinks = page.locator("article a[href^='/listings/']");
  await expect(cardLinks.first()).toBeVisible();
  const firstPage = await cardLinks.evaluateAll((links) =>
    links.map((link) => link.getAttribute("href")),
  );
  const next = page.getByRole("button", { name: /Дараах/ });
  test.skip(await next.isDisabled(), "Dataset has only one marketplace page");

  await next.click();
  await expect(page.getByText("2-р хуудас", { exact: true })).toBeVisible();
  const secondPage = await cardLinks.evaluateAll((links) =>
    links.map((link) => link.getAttribute("href")),
  );
  expect(secondPage.filter((href) => firstPage.includes(href))).toEqual([]);
});

test("@mobile filter opens as a dismissible modal drawer", async ({ page }) => {
  await page.goto("/sale");
  await page.getByRole("button", { name: /Зар шүүх/ }).click();
  const dialog = page.getByRole("dialog", { name: "Зар шүүх" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("Дүүрэг")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
});
