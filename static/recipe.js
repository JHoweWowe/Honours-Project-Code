// Ingredient servings scaler and metric/imperial unit converter

// --- Number parsing helpers ---

const UNICODE_FRACTIONS = {
    '½': 0.5,   // ½
    '¼': 0.25,  // ¼
    '¾': 0.75,  // ¾
    '⅓': 1/3,   // ⅓
    '⅔': 2/3,   // ⅔
    '⅛': 0.125, // ⅛
    '⅜': 0.375, // ⅜
    '⅝': 0.625, // ⅝
    '⅞': 0.875, // ⅞
};

function parseNum(str) {
    str = String(str);
    for (const [sym, val] of Object.entries(UNICODE_FRACTIONS)) {
        str = str.replace(sym, String(val));
    }
    // "1 1/2" mixed numbers
    str = str.replace(/(\d+)\s+(\d+)\/(\d+)/, (_, w, n, d) => String(+w + +n / +d));
    // "1/2" fractions
    str = str.replace(/(\d+)\/(\d+)/, (_, n, d) => String(+n / +d));
    return parseFloat(str);
}

// Re-express a number as a friendly string (whole + unicode fraction where sensible)
const FRACTION_SYMS = [
    [0.125, '⅛'], [0.25, '¼'], [0.333, '⅓'],
    [0.5, '½'],   [0.667, '⅔'], [0.75, '¾'],
];

function fmtNum(n) {
    if (n <= 0) return '0';
    const whole = Math.floor(n);
    const frac  = n - whole;
    for (const [val, sym] of FRACTION_SYMS) {
        if (Math.abs(frac - val) < 0.05) {
            return whole > 0 ? `${whole}${sym}` : sym;
        }
    }
    const rounded = Math.round(n * 10) / 10;
    return rounded === Math.round(rounded) ? String(Math.round(rounded)) : rounded.toFixed(1);
}

// Scale all leading numeric tokens (including unicode fractions) in ingredient text
function scaleText(text, ratio) {
    // Match: optional unicode fraction chars and/or digits, optional slash-fraction
    const numPattern = /([½¼¾⅓⅔⅛⅜⅝⅞\d]+(?:\.\d+)?(?:\s*\d+\/\d+)?)/;
    return text.replace(
        new RegExp(numPattern.source, 'g'),
        (match) => {
            const val = parseNum(match);
            if (isNaN(val) || val === 0) return match;
            return fmtNum(val * ratio);
        }
    );
}

// --- Unit conversion (metric → imperial) ---

const METRIC_UNITS = {
    'kg':     { to: 'lb',    f: 2.20462 },
    'g':      { to: 'oz',    f: 0.03527 },
    'litre':  { to: 'pint',  f: 1.75975 },
    'litres': { to: 'pints', f: 1.75975 },
    'liter':  { to: 'pint',  f: 1.75975 },
    'liters': { to: 'pints', f: 1.75975 },
    'l':      { to: 'pt',    f: 1.75975 },
    'ml':     { to: 'fl oz', f: 0.03381 },
    'cm':     { to: 'in',    f: 0.39370 },
};

function toImperial(text) {
    let result = text;
    for (const [unit, { to, f }] of Object.entries(METRIC_UNITS)) {
        result = result.replace(
            new RegExp(`(\\d+(?:[.,]\\d+)?)\\s*${unit}\\b`, 'gi'),
            (_, num) => `${fmtNum(parseFloat(num.replace(',', '.')) * f)} ${to}`
        );
    }
    return result;
}

// --- DOM wiring ---

const servingsInput = document.getElementById('servings-input');
const unitToggle    = document.getElementById('flexSwitchCheckChecked');
const unitLabel     = document.getElementById('flexSwitchCheckCheckedLabel');
const ingredientEls = document.querySelectorAll('.ingredient-item');

const defaultServings = servingsInput ? parseInt(servingsInput.dataset.default, 10) || 1 : 1;
// Capture original text once from the DOM
const originalTexts = Array.from(ingredientEls).map(el => el.textContent.trim());

let imperial = false;

if (unitLabel) unitLabel.textContent = 'Metric';

function refreshIngredients() {
    const ratio = servingsInput
        ? (parseInt(servingsInput.value, 10) || defaultServings) / defaultServings
        : 1;

    ingredientEls.forEach((el, i) => {
        let text = scaleText(originalTexts[i], ratio);
        if (imperial) text = toImperial(text);
        el.textContent = text;
    });
}

if (servingsInput) {
    servingsInput.addEventListener('input', function () {
        const v = parseInt(this.value, 10);
        if (v < 1) this.value = 1;
        if (v > 99) this.value = 99;
        refreshIngredients();
        refreshPrice();
    });
}

if (unitToggle) {
    unitToggle.addEventListener('change', function () {
        imperial = !this.checked;
        if (unitLabel) unitLabel.textContent = this.checked ? 'Metric' : 'Imperial';
        refreshIngredients();
    });
}

// --- Price scaling + currency conversion (static rates, base GBP) ---

const EXCHANGE_RATES   = { GBP: 1, USD: 1.26, EUR: 1.17, SGD: 1.68 };
const CURRENCY_SYMBOLS = { GBP: '£', USD: '$', EUR: '€', SGD: 'S$' };

const currencySelect  = document.getElementById('currency-select');
const pricePerServing = document.getElementById('price-per-serving');
const priceTotal      = document.getElementById('price-total');
const ingrCostEls     = document.querySelectorAll('.ingr-cost-val');

function refreshPrice() {
    const ratio    = servingsInput
        ? (parseInt(servingsInput.value, 10) || defaultServings) / defaultServings
        : 1;
    const currency = currencySelect ? currencySelect.value : 'GBP';
    const rate     = EXCHANGE_RATES[currency] || 1;
    const sym      = CURRENCY_SYMBOLS[currency] || '£';

    if (pricePerServing) {
        const base = parseFloat(pricePerServing.dataset.gbp);
        if (!isNaN(base)) pricePerServing.textContent = sym + (base * rate).toFixed(2);
    }
    if (priceTotal) {
        const base = parseFloat(priceTotal.dataset.gbp);
        if (!isNaN(base)) priceTotal.textContent = sym + (base * ratio * rate).toFixed(2);
    }
    ingrCostEls.forEach(el => {
        const base = parseFloat(el.dataset.gbp);
        if (!isNaN(base)) el.textContent = sym + (base * ratio * rate).toFixed(2);
    });
}

if (currencySelect) currencySelect.addEventListener('change', refreshPrice);
refreshPrice();
