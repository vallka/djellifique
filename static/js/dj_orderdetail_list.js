(() => {
  "use strict";

  // ---- Config ----
  const STATUS_UPDATE_URL = "/api/v1/prestashop/order/updatestatus/";
  const STATUS_ID_READY = 39;

  // ⚠️ Don't keep real tokens in frontend JS.
  const API_TOKEN = "Token 6b246cc18769c6ec02dc20009649d5ae5903d454";

  // ---- State ----
  let idOrder = null;
  /** @type {Record<string, [number, number]>} */
  let order = {};

  // ---- Helpers ----
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function lsKeyOrder(id) { return `o${id}`; }
  function lsKeyReady(id) { return `o${id}-ready`; }

  function parseIntSafe(text) {
    const n = parseInt(String(text ?? "").trim(), 10);
    return Number.isFinite(n) ? n : 0;
  }

  function loadOrderFromStorage() {
    try {
      const raw = window.localStorage.getItem(lsKeyOrder(idOrder));
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return (parsed && typeof parsed === "object") ? parsed : {};
    } catch {
      return {};
    }
  }

  function saveOrderToStorage() {
    window.localStorage.setItem(lsKeyOrder(idOrder), JSON.stringify(order));
  }

  function setRowVisualState(rowEl, productQty, readyQty) {
    const checkboxWrap = rowEl.querySelector(".checkbox");
    const checkbox = rowEl.querySelector('input[type="checkbox"]');
    const readyQtyEl = rowEl.querySelector(".ready_quantity");

    if (readyQtyEl) readyQtyEl.textContent = String(readyQty);

    const isReady = readyQty === productQty;
    const isHalf = readyQty > 0 && readyQty < productQty;

    if (checkboxWrap) {
      checkboxWrap.classList.toggle("ready", isReady);
      checkboxWrap.classList.toggle("half_ready", isHalf);
      checkboxWrap.classList.toggle("not_ready", !isReady && !isHalf);
    }

    // Your original UI: checkbox is checked only when fully ready.
    if (checkbox) checkbox.checked = isReady;
  }

  function initRowFromState(rowEl) {
    const productQty = parseIntSafe(qs(".product_quantity", rowEl)?.textContent);
    const idProduct = "p" + (rowEl.getAttribute("data-id_product") || "");

    if (!idProduct || idProduct === "p") return;

    // Ensure stored structure exists: [productQty, readyQty]
    if (order[idProduct]) {
      // Keep product qty in sync with DOM
      if (order[idProduct][0] !== productQty) order[idProduct][0] = productQty;
    } else {
      order[idProduct] = [productQty, 0];
    }

    const readyQty = parseIntSafe(order[idProduct][1]);
    setRowVisualState(rowEl, productQty, readyQty);
  }

  function updateOrder(idProduct, productQuantity, readyQuantity) {
    console.log("updateOrder:", idProduct, productQuantity, readyQuantity);

    // Update in-memory state
    order[idProduct] = [productQuantity, readyQuantity];
    saveOrderToStorage();

    // Persist
    //localStorage.setItem("o" + id_order, JSON.stringify(order));

    // Count non-pack product rows in DOM
    const productRows = document.querySelectorAll(".product_row");
    const packRows = document.querySelectorAll(".product_row.gel_row_pack");
    const nProducts = productRows.length - packRows.length;

    // Build a Set of pack product IDs so we can exclude them from "ready" count
    const packIds = new Set(
      Array.from(packRows)
        .map((row) => row.getAttribute("data-id_product"))
        .filter(Boolean)
        .map((id) => "p" + id)
    );

    // Count ready items among NON-pack rows only
    let ready = 0;
    for (const [key, element] of Object.entries(order)) {
      if (!Array.isArray(element)) continue;
      if (packIds.has(key)) continue; // exclude pack content

      const [qty, rdy] = element;
      if (qty === rdy) ready += 1;
    }

    const btn = document.getElementById("btn-update-status");

    if (ready && nProducts === ready) {
      console.log("+ready", ready, nProducts);
      window.localStorage.setItem(lsKeyReady(idOrder), "1");
      if (btn) btn.style.display = "";
    } else {
      console.log("-not ready", ready, nProducts);
      window.localStorage.removeItem(lsKeyReady(idOrder));
      if (btn) btn.style.display = "none";
    }
  }

  async function updateOrderStatusOnServer() {
    const resp = await fetch(STATUS_UPDATE_URL, {
      method: "POST",
      headers: {
        "Authorization": API_TOKEN,
        // If your API expects JSON instead of form encoding, switch accordingly.
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body: new URLSearchParams({
        id_order: String(idOrder),
        id_status: String(STATUS_ID_READY),
      }),
    });

    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Status update failed: ${resp.status} ${resp.statusText} ${text}`);
    }

    return resp.json().catch(() => ({}));
  }

  // ---- Main ----
  document.addEventListener("DOMContentLoaded", () => {
    const table = qs(".gel_table");
    idOrder = table?.getAttribute("data-id_order") || table?.dataset?.id_order || null;

    if (!idOrder) {
      console.warn("No .gel_table[data-id_order] found; order detail JS not initialized.");
      return;
    }

    order = loadOrderFromStorage();

    // Show button if previously flagged ready
    if (window.localStorage.getItem(lsKeyReady(idOrder))) {
      const btn = qs("#btn-update-status");
      if (btn) btn.style.display = "";
    }

    // Init rows
    const rows = qsa(".product_row");
    rows.forEach(initRowFromState);

    saveOrderToStorage();

    // Checkbox click/changes (delegate)
    document.addEventListener("change", (e) => {
      const checkbox = e.target instanceof HTMLInputElement
        ? e.target
        : null;

      if (!checkbox || checkbox.type !== "checkbox") return;

      const row = checkbox.closest(".gel_row, .product_row");
      if (!row) return;

      const idProduct = "p" + (row.getAttribute("data-id_product") || "");
      const productQty = parseIntSafe(qs(".product_quantity", row)?.textContent);
      let readyQty = parseIntSafe(qs(".ready_quantity", row)?.textContent);

      if (!idProduct || idProduct === "p") return;

      // Original behavior:
      // - When user checks: increment readyQty by 1 up to productQty.
      // - Checkbox only stays checked if readyQty == productQty; otherwise revert it.
      // - When user unchecks: prevent going below 1 if readyQty > 0 (force checked).
      if (checkbox.checked) {
        if (readyQty < productQty) {
          readyQty += 1;
          updateOrder(idProduct, productQty, readyQty);
        }

        // Recompute UI state; checkbox is only checked when fully ready
        setRowVisualState(row, productQty, readyQty);

      } else {
        // Disallow unchecking when there is any ready quantity
        if (readyQty > 0) {
          checkbox.checked = (readyQty === productQty);
          // Keep visuals consistent
          setRowVisualState(row, productQty, readyQty);
        }
      }
    });

    // Reset button
    const btnReset = qs("#btn-reset");
    if (btnReset) {
      btnReset.addEventListener("click", () => {
        if (!confirm("Are you sure you want to reset the order?")) return;

        order = {};

        qsa(".product_row").forEach((row) => {
          const productQty = parseIntSafe(qs(".product_quantity", row)?.textContent);
          const idProduct = "p" + (row.getAttribute("data-id_product") || "");
          if (idProduct && idProduct !== "p") order[idProduct] = [productQty, 0];
          setRowVisualState(row, productQty, 0);
        });

        window.localStorage.removeItem(lsKeyOrder(idOrder));
        window.localStorage.removeItem(lsKeyReady(idOrder));

        const btnUpdate = qs("#btn-update-status");
        if (btnUpdate) btnUpdate.style.display = "none";

        // remove focus from Reset button
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      });
    }

    // Update status button
    const btnUpdate = qs("#btn-update-status");
    if (btnUpdate) {
      btnUpdate.addEventListener("click", async () => {
        try {
          await updateOrderStatusOnServer();
          document.location.href = "/prestashop/order/";
        } catch (err) {
          console.error(err);
          alert("Failed to update order status. Check console for details.");
        }
      });
    }

    // Your original call
    if (typeof window.setup_video === "function") {
      window.setup_video();
    }
  });
})();