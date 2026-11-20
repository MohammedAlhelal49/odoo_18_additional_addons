/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { unaccent } from "@web/core/utils/strings";

const CODE_FIELDS = ["barcode", "default_code"];
const NAME_FIELDS = ["display_name", "x_name_ar", "x_name_en"];

// توحيد الحروف العربية: أ إ آ ٱ ← ا، ة ← ه، ى ئ ← ي، ؤ ← و، وحذف التشكيل والتطويل
const ARABIC_MAP = { "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ئ": "ي", "ؤ": "و" };
const ARABIC_RE = /[أإآٱةىئؤ]/g;
const HARAKAT_RE = /[ً-ٰٟـ]/g;
// الأرقام العربية (٠-٩ و ۰-۹) ← 0-9
const DIGITS_RE = /[٠-٩۰-۹]/g;
// كل شي غير حرف أو رقم (مسافات، - / . إلخ)
const SEPARATORS_RE = /[^\p{L}\p{N}]+/gu;

function normalize(value) {
    return unaccent(String(value || "").toLowerCase(), false)
        .replace(HARAKAT_RE, "")
        .replace(ARABIC_RE, (ch) => ARABIC_MAP[ch])
        .replace(DIGITS_RE, (ch) => String((ch.charCodeAt(0) & 0xf) % 10))
        .trim();
}

// بدون مسافات ورموز: "iPhone 13" و "CC-18H" بيصيروا "iphone13" و "cc18h"
function compact(value) {
    return normalize(value).replace(SEPARATORS_RE, "");
}

// الاسم بدون "[الكود] " اللي بيضيفه أودو بأوله (الكود بينبحث فيه لحاله)
function productName(product, field) {
    const value = product[field] || "";
    return field === "display_name" ? value.replace(/^\[[^\]]*\]\s*/, "") : value;
}

// فهرس البحث لكل منتج، بينحسب مرة وحدة بالجلسة
const searchIndex = new Map();

function getIndex(product) {
    const source = [...NAME_FIELDS, ...CODE_FIELDS].map((field) => product[field] || "").join("\u0001");
    let index = searchIndex.get(product.id);
    if (!index || index.source !== source) {
        const names = NAME_FIELDS.map((field) => normalize(productName(product, field))).filter(Boolean);
        const codes = CODE_FIELDS.map((field) => compact(product[field])).filter(Boolean);
        index = {
            source,
            codes,
            names: names.map((name) => name.replace(SEPARATORS_RE, "")),
            words: names.flatMap((name) => name.split(SEPARATORS_RE)).filter(Boolean),
            text: [...names.map((name) => name.replace(SEPARATORS_RE, "")), ...codes].join(" "),
        };
        searchIndex.set(product.id, index);
    }
    return index;
}

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        // تجهيز فهرس البحث على دفعات بعد فتح الشاشة، حتى ما يتأخر أول بحث
        const products = this.products;
        let start = 0;
        const warm = () => {
            const end = Math.min(start + 500, products.length);
            for (; start < end; start++) {
                getIndex(products[start]);
            }
            if (start < products.length) {
                setTimeout(warm, 0);
            }
        };
        setTimeout(warm, 0);
    },

    getProductsBySearchWord(searchWord) {
        const query = compact(searchWord);
        if (!query) {
            return super.getProductsBySearchWord(searchWord);
        }

        // 1) الباركود أو الكود كامل: المنتج تبعه بس
        const codeMatches = this.products.filter((product) => getIndex(product).codes.includes(query));
        if (codeMatches.length) {
            return codeMatches;
        }

        // 2) بحث ذكي: كل جزء مكتوب لازم يكون موجود بالاسم (عربي أو إنكليزي) أو الكود،
        //    بأي ترتيب، وجزء من كلمة أو من الكود بيكفي
        const tokens = normalize(searchWord).split(SEPARATORS_RE).filter(Boolean);
        const results = [];
        for (const product of this.products) {
            const index = getIndex(product);
            if (tokens.every((token) => index.text.includes(token))) {
                results.push({ product, rank: this._smartSearchRank(index, query, tokens) });
            }
        }

        // 3) الترتيب: الأقرب أولاً
        results.sort((a, b) => {
            for (let i = 0; i < a.rank.length; i++) {
                if (a.rank[i] !== b.rank[i]) {
                    return a.rank[i] - b.rank[i];
                }
            }
            return a.product.display_name.localeCompare(b.product.display_name);
        });
        return results.map((result) => result.product);
    },

    // البحث بالسيرفر (Enter أو "بحث أكثر") للمنتجات اللي مش محمّلة بنقطة البيع:
    // كل كلمة لحالها بأي ترتيب، بالاسم الإنكليزي والعربي والكود والباركود
    loadProductFromDBDomain(searchProductWord) {
        const tokens = normalize(searchProductWord).split(SEPARATORS_RE).filter(Boolean);
        if (!tokens.length) {
            return super.loadProductFromDBDomain(searchProductWord);
        }
        const domain = [];
        for (const token of tokens) {
            // الحروف العربية اللي إلها أكتر من شكل بتصير "_" (أي حرف)، وبين الحروف والأرقام
            // "%" حتى "iphone13" تلاقي "iPhone 13"
            const pattern = token
                .replace(/[اهيو]/g, "_")
                .replace(/(\p{L})(?=\p{N})|(\p{N})(?=\p{L})/gu, "$1$2%");
            domain.push(
                "|", "|", "|",
                ["name", "ilike", pattern],
                ["arabic_name", "ilike", pattern],
                ["default_code", "ilike", pattern],
                ["barcode", "ilike", pattern]
            );
        }
        domain.push(["available_in_pos", "=", true], ["sale_ok", "=", true]);
        return domain;
    },

    _smartSearchRank(index, query, tokens) {
        const codeStarts = index.codes.some((code) => code.startsWith(query)) ? 0 : 1;
        const nameStarts = index.names.some((name) => name.startsWith(query)) ? 0 : 1;
        const tokensInside = tokens.filter((token) => !index.words.some((word) => word.startsWith(token))).length;
        const exactWords = tokens.filter((token) => index.words.includes(token)).length;
        const position = Math.min(...index.names.map((name) => {
            const at = name.indexOf(tokens[0]);
            return at === -1 ? Infinity : at;
        }));
        return [codeStarts, nameStarts, tokensInside, -exactWords, position, index.names[0]?.length || 0];
    },
});
