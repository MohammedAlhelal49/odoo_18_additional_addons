/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { parseFloat } from "@web/views/fields/parsers";

// ============================================================
// Helper: ترجمة ثنائية عربي / إنجليزي
// ============================================================
function t(en, ar) {
    const lang = luxon.Settings.defaultLocale?.split("-")[0] || "en";
    return lang === "ar" ? ar : en;
}

// ============================================================
// Helper: نوع التقييد من إعدادات نقطة البيع (alert / block / false)
// ============================================================
function getRestrictionType(pos) {
    if (!pos.config.stock_restriction_enabled) {
        return false;
    }
    return pos.config.stock_restriction_type || false;
}

// ============================================================
// Helper: فقط المنتجات اللي بيتتبّع مخزونها
// ============================================================
function isStockTracked(product) {
    return Boolean(product?.is_storable);
}

function formatQty(qty) {
    return String(Math.round((qty || 0) * 1000) / 1000);
}

// ============================================================
// Helper: مجموع كمية المنتج بالطلب (بالوحدة الأساسية)
// كمية السطر مخزّنة أصلاً بالوحدة الأساسية (dekad_pos_sale_enhancement
// بيحوّل كمية الوحدة البديلة قبل ما يخزّنها).
// ============================================================
function qtyInOrder(order, product, excludeLine = null) {
    if (!order) {
        return 0;
    }
    return order.get_orderlines().reduce((sum, line) => {
        if (line === excludeLine || line.get_product()?.id !== product.id) {
            return sum;
        }
        return sum + line.get_quantity();
    }, 0);
}

// ============================================================
// Helper: تحويل كمية مكتوبة على سطر لوحدة المنتج الأساسية
// (نفس منطق set_quantity بموديول dekad_pos_sale_enhancement)
// ============================================================
function toBaseQty(line, qty) {
    const uom = line.uom_rec_id;
    if (uom && uom.uom_type === "bigger") {
        return qty * uom.factor_inv;
    }
    if (uom && uom.uom_type === "smaller") {
        return qty * uom.factor;
    }
    return qty;
}

// ============================================================
// Helper: تحديث الكمية المتوفرة من السيرفر (طلب واحد لكل المنتجات)
// إذا فشل الطلب (مثلاً انقطاع النت) منكمّل بالكمية المخزّنة.
// ============================================================
async function refreshStock(pos, products) {
    if (!products.length) {
        return;
    }
    try {
        const result = await pos.data.call("product.product", "get_pos_stock_qty", [
            products.map((p) => p.id),
            pos.config.id,
        ]);
        for (const product of products) {
            const qty = result?.[product.id] ?? result?.[String(product.id)];
            if (qty !== undefined) {
                product.qty_available = qty;
            }
        }
    } catch {
        // offline: keep the cached quantity
    }
}

// ============================================================
// قبول التنبيه (Alert) لمنتج بطلب معيّن، حتى ما يتكرر التنبيه
// ============================================================
const acceptedByOrder = new WeakMap();

function isAccepted(order, product) {
    return Boolean(order && acceptedByOrder.get(order)?.has(product.id));
}

function markAccepted(order, products) {
    if (!order) {
        return;
    }
    if (!acceptedByOrder.has(order)) {
        acceptedByOrder.set(order, new Set());
    }
    const accepted = acceptedByOrder.get(order);
    for (const product of products) {
        accepted.add(product.id);
    }
}

function problemLine(product, available, requested) {
    return (
        `• ${product.display_name}` +
        `  (${t("Available", "متوفر")}: ${formatQty(available)} | ` +
        `${t("Requested", "مطلوب")}: ${formatQty(requested)})`
    );
}

// ============================================================
// عرض المنع أو التنبيه. بيرجع true إذا مسموح نكمّل
// ============================================================
async function handleStockIssue(pos, type, messages, order, products) {
    const list = messages.join("\n");
    if (type === "block") {
        pos.dialog.add(AlertDialog, {
            title: t("Not enough stock", "الكمية غير متوفرة"),
            body:
                t("The following products exceed the available quantity:", "المواد التالية تتجاوز الكمية المتوفرة:") +
                "\n\n" + list,
        });
        return false;
    }
    const confirmed = await ask(pos.dialog, {
        title: t("Stock Warning", "تنبيه مخزون"),
        body:
            t("The following products exceed the available quantity:", "المواد التالية تتجاوز الكمية المتوفرة:") +
            "\n\n" + list + "\n\n" +
            t("Do you want to proceed anyway?", "هل تريد المتابعة رغم ذلك؟"),
    });
    if (confirmed) {
        markAccepted(order, products);
    }
    return Boolean(confirmed);
}

// ============================================================
// Patch 1: عند إضافة منتج (كبسة على المنتج أو باركود)
// ============================================================
patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const allowed = await this._checkStockBeforeAdd(vals);
        if (!allowed) {
            return;
        }
        return await super.addLineToCurrentOrder(vals, opts, configure);
    },

    async _checkStockBeforeAdd(vals) {
        const type = getRestrictionType(this);
        if (!type) {
            return true;
        }
        let product = vals.product_id;
        if (typeof product === "number") {
            product = this.models["product.product"].get(product);
        }
        // منتج بعدة نسخ: النسخة بتنختار بعدين، فبينفحص وقت الدفع
        if (!isStockTracked(product) || product.isConfigurable?.()) {
            return true;
        }

        const order = this.get_order();
        await refreshStock(this, [product]);
        const available = product.qty_available ?? 0;
        const requested = qtyInOrder(order, product) + (vals.qty ?? 1);
        if (requested <= available || (type === "alert" && isAccepted(order, product))) {
            return true;
        }
        return await handleStockIssue(
            this, type, [problemLine(product, available, requested)], order, [product]
        );
    },

    // ============================================================
    // Patch 2: عند الضغط على Payment — فحص نهائي لكل الطلب
    // ============================================================
    async pay() {
        const type = getRestrictionType(this);
        const order = this.get_order();
        if (type && order) {
            const totals = new Map();
            for (const line of order.get_orderlines()) {
                const product = line.get_product();
                if (isStockTracked(product)) {
                    totals.set(product, (totals.get(product) || 0) + line.get_quantity());
                }
            }
            await refreshStock(this, [...totals.keys()]);

            const products = [];
            const messages = [];
            for (const [product, requested] of totals) {
                const available = product.qty_available ?? 0;
                if (requested <= 0 || requested <= available) {
                    continue;
                }
                if (type === "alert" && isAccepted(order, product)) {
                    continue;
                }
                products.push(product);
                messages.push(problemLine(product, available, requested));
            }
            if (messages.length) {
                const allowed = await handleStockIssue(this, type, messages, order, products);
                if (!allowed) {
                    return;
                }
            }
        }
        return super.pay(...arguments);
    },
});

// ============================================================
// Patch 3: تعديل الكمية من الـ numpad + عرض المتبقي بسطر الطلب
// ============================================================
patch(OrderSummary.prototype, {
    _setValue(val) {
        const type = getRestrictionType(this.pos);
        const order = this.currentOrder;
        const line = order?.get_selected_orderline();
        if (
            !type ||
            this.pos.numpadMode !== "quantity" ||
            val === "remove" ||
            !line ||
            line.combo_parent_id
        ) {
            return super._setValue(val);
        }
        const product = line.get_product();
        if (!isStockTracked(product)) {
            return super._setValue(val);
        }

        let typed;
        try {
            typed = typeof val === "number" ? val : parseFloat(val);
        } catch {
            return super._setValue(val);
        }
        const newQty = toBaseQty(line, typed);
        // التنقيص دايماً مسموح
        if (isNaN(newQty) || newQty <= line.get_quantity()) {
            return super._setValue(val);
        }

        const available = product.qty_available ?? 0;
        const requested = qtyInOrder(order, product, line) + newQty;
        if (requested <= available || (type === "alert" && isAccepted(order, product))) {
            return super._setValue(val);
        }

        const messages = [problemLine(product, available, requested)];
        handleStockIssue(this.pos, type, messages, order, [product]).then((allowed) => {
            if (allowed) {
                super._setValue(val);
            } else {
                this.numberBuffer.reset();
            }
        });
    },

    getStockRemaining(line) {
        if (!getRestrictionType(this.pos)) {
            return null;
        }
        const product = line.get_product();
        if (!isStockTracked(product) || line.combo_parent_id) {
            return null;
        }
        const remaining = (product.qty_available ?? 0) - qtyInOrder(this.currentOrder, product);
        return {
            label: t("Remaining in stock", "المتبقي بالمخزون"),
            value: formatQty(remaining),
            // صفر أو أقل: أحمر — من 1 لـ 5: برتقالي — أكتر من 5: رمادي
            cssClass: remaining > 5 ? "text-muted" : "fw-bold",
            style: remaining <= 0 ? "color: #dc3545;" : remaining <= 5 ? "color: #fd7e14;" : "",
        };
    },
});
