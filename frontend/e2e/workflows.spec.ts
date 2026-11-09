import { test, expect, type Locator } from "@playwright/test"
async function choose(select: Locator, text: string) {
  const value = await select
    .locator("option")
    .filter({ hasText: text })
    .first()
    .getAttribute("value")
  await select.selectOption(value!)
}
test("Urdu login, a persisted repair receipt, payment, PDF and responsive navigation", async ({
  page,
  isMobile,
}, testInfo) => {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { name: "خوش آمدید", exact: true })
  ).toBeVisible()
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl")
  await page.getByLabel("صارف کا نام", { exact: true }).fill("e2e_owner")
  await page
    .getByLabel("پاس ورڈ", { exact: true })
    .fill("test-only-long-password-2026")
  await page.getByRole("button", { name: "لاگ اِن کریں", exact: true }).click()
  await expect(
    page.getByRole("heading", { name: "کاروبار کا جائزہ" })
  ).toBeVisible()
  await page.getByRole("button", { name: "English", exact: true }).click()
  await expect(
    page.getByRole("heading", { name: "Business overview" })
  ).toBeVisible()
  await page.screenshot({
    path: `../.runtime/dashboard-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.goto("/new-receipt")
  await page
    .getByLabel("Equipment / service", { exact: true })
    .fill(`موٹر مرمت Motor ${Date.now()}`)
  await page.getByLabel("Unit price (Rs.)", { exact: true }).fill("15000")
  await page.getByLabel("Initial amount received", { exact: true }).fill("5000")
  await page.getByRole("button", { name: "Save and post", exact: true }).click()
  await expect(page).toHaveURL(/\/receipts\/[0-9a-f-]+$/)
  const receiptUrl = page.url()
  await expect(page.getByText("Rs. 10,000.00", { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByText("Rs. 10,000.00", { exact: true })).toBeVisible()
  const download = page.waitForEvent("download")
  await page.getByRole("link", { name: "Download PDF" }).click()
  expect((await download).suggestedFilename()).toMatch(/^receipt-\d+\.pdf$/)
  await page
    .getByRole("button", { name: "Record payment", exact: true })
    .click()
  await page.getByLabel("Amount", { exact: true }).fill("10000")
  await page.getByRole("button", { name: "Save payment", exact: true }).click()
  await expect(page.getByText("Rs. 0.00", { exact: true })).toBeVisible()
  await page
    .getByRole("button", { name: "Mark repair complete", exact: true })
    .click()
  await expect(
    page.getByRole("button", { name: "Mark repair complete", exact: true })
  ).toHaveCount(0)
  if (isMobile)
    await page.getByRole("button", { name: "Toggle navigation" }).click()
  await page.getByRole("link", { name: "Receipt records", exact: true }).click()
  await expect(
    page.getByRole("heading", { name: "Receipt records", exact: true })
  ).toBeVisible()
  await page.goto(receiptUrl)
  await expect(page.getByText("Rs. 0.00", { exact: true })).toBeVisible()
  await page.screenshot({
    path: `../.runtime/receipt-${testInfo.project.name}.png`,
    fullPage: true,
  })
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 2
  )
  expect(overflow).toBe(false)
  await page.evaluate(() => {
    window.print = () => {
      throw new Error("Printer unavailable")
    }
  })
  await page.getByRole("button", { name: "Print", exact: true }).click()
  await expect(page.getByRole("status")).toContainText(
    "Printing is unavailable"
  )
  await page.reload()
  await expect(page.getByText("Rs. 0.00", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "اردو", exact: true }).click()
  await expect(
    page.getByRole("columnheader", { name: "تفصیل", exact: true })
  ).toBeVisible()
  await page.screenshot({
    path: `../.runtime/receipt-urdu-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.pdf({
    path: `../.runtime/browser-print-${testInfo.project.name}.pdf`,
    format: "A4",
    printBackground: true,
  })
})

test("customer, purchase, sale and completed worker payroll persist through the interface", async ({
  page,
}) => {
  await page.goto("/")
  await page.getByLabel("صارف کا نام", { exact: true }).fill("e2e_owner")
  await page
    .getByLabel("پاس ورڈ", { exact: true })
    .fill("test-only-long-password-2026")
  await page.getByRole("button", { name: "لاگ اِن کریں", exact: true }).click()
  await expect(
    page.getByRole("heading", { name: "کاروبار کا جائزہ" })
  ).toBeVisible()
  await page.getByRole("button", { name: "English", exact: true }).click()
  const suffix = String(Date.now())
  await page.goto("/customers")
  await page.getByRole("button", { name: "New record" }).click()
  await page.getByRole("dialog").getByLabel(/^Name/).fill(`Ahmed ${suffix}`)
  await page
    .getByRole("dialog")
    .getByLabel("Phone", { exact: true })
    .fill("03001234567")
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click()
  await expect(
    page.getByRole("cell", { name: `Ahmed ${suffix}`, exact: true })
  ).toBeVisible()
  await page.goto("/inventory")
  await page.getByRole("button", { name: "New record" }).click()
  await page
    .getByRole("dialog")
    .getByLabel(/^Inventory code/)
    .fill(`M${suffix}`)
  await page
    .getByRole("dialog")
    .getByLabel(/^Equipment name/)
    .fill(`Motor ${suffix}`)
  await page
    .getByRole("dialog")
    .getByLabel(/^Category/)
    .fill("Motor")
  await page
    .getByRole("dialog")
    .getByLabel(/^Selling price/)
    .fill("3000")
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click()
  await expect(
    page.getByRole("cell", { name: `M${suffix}`, exact: true })
  ).toBeVisible()
  await page.goto("/new-receipt")
  await page
    .getByRole("combobox", { name: "Transaction type", exact: true })
    .selectOption("purchase")
  await choose(
    page.getByRole("combobox", { name: "Inventory item", exact: true }),
    `M${suffix} Motor ${suffix}`
  )
  await page.getByLabel("Quantity", { exact: true }).fill("3")
  await page.getByLabel("Unit price (Rs.)", { exact: true }).fill("1000")
  await page.getByRole("button", { name: "Save and post", exact: true }).click()
  await expect(page).toHaveURL(/\/receipts\/[0-9a-f-]+$/)
  await page.goto("/new-receipt")
  await page
    .getByRole("combobox", { name: "Transaction type", exact: true })
    .selectOption("sale")
  await choose(
    page.getByRole("combobox", { name: "Inventory item", exact: true }),
    `M${suffix} Motor ${suffix}`
  )
  await page.getByLabel("Initial amount received", { exact: true }).fill("3000")
  await page.getByRole("button", { name: "Save and post", exact: true }).click()
  await expect(page).toHaveURL(/\/receipts\/[0-9a-f-]+$/)
  await expect(page.getByText("Rs. 0.00", { exact: true })).toBeVisible()
  await page.goto("/workers")
  await page.getByRole("button", { name: "New record" }).click()
  await page
    .getByRole("dialog")
    .getByLabel(/^Worker code/)
    .fill(`W${suffix}`)
  await page.getByRole("dialog").getByLabel(/^Name/).fill(`Worker ${suffix}`)
  await page
    .getByRole("dialog")
    .getByLabel(/^Specialization/)
    .fill("Motor repair")
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click()
  await expect(
    page.getByRole("cell", { name: `W${suffix}`, exact: true })
  ).toBeVisible()
  await page.goto("/new-receipt")
  await page
    .getByLabel("Equipment / service", { exact: true })
    .fill(`Repair ${suffix}`)
  await page.getByLabel("Unit price (Rs.)", { exact: true }).fill("15000")
  await page.getByRole("button", { name: "Save and post", exact: true }).click()
  await expect(page).toHaveURL(/\/receipts\/[0-9a-f-]+$/)
  const number = (
    await page
      .getByRole("heading", { name: /^Receipt / })
      .first()
      .innerText()
  ).split(" ")[1]
  await page.goto("/workers")
  await page.getByRole("button", { name: "Assign job", exact: true }).click()
  const receiptSelect = page
    .getByRole("dialog")
    .getByRole("combobox", { name: "Receipt", exact: true })
  const receiptValue = await receiptSelect
    .locator("option")
    .filter({ hasText: number })
    .getAttribute("value")
  await receiptSelect.selectOption(receiptValue!)
  await page
    .getByRole("combobox", { name: "Equipment", exact: true })
    .selectOption({ label: `Repair ${suffix}` })
  await choose(
    page
      .getByRole("dialog")
      .getByRole("combobox", { name: "Worker", exact: true }),
    `W${suffix} Worker ${suffix}`
  )
  await page
    .getByLabel("Work description", { exact: true })
    .fill(`Winding ${suffix}`)
  await page.getByLabel("Labor amount", { exact: true }).fill("1500")
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Assign job", exact: true })
    .click()
  const job = page.getByRole("row").filter({ hasText: `Winding ${suffix}` })
  await expect(job).toBeVisible()
  page.once("dialog", (dialog) => dialog.accept())
  await job.getByRole("button", { name: "Complete", exact: true }).click()
  await expect(job.getByText("Completed", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "Pay worker", exact: true }).click()
  await choose(
    page
      .getByRole("dialog")
      .getByRole("combobox", { name: "Worker", exact: true }),
    `W${suffix} Worker ${suffix}`
  )
  await page
    .getByRole("dialog")
    .getByLabel("Amount", { exact: true })
    .fill("500")
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save payment", exact: true })
    .click()
  await expect(page.getByRole("dialog")).toHaveCount(0)
  await page.getByRole("button", { name: "Workers", exact: true }).click()
  const worker = page.getByRole("row").filter({ hasText: `W${suffix}` })
  await worker.getByRole("button", { name: "History", exact: true }).click()
  await expect(
    page.getByRole("dialog").getByText("Payable: Rs. 1,000.00")
  ).toBeVisible()
})
