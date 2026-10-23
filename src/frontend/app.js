/**
 * Orquestación de la Interfaz de Usuario Web (Vanilla JavaScript ES6+).
 * Conecta el catálogo comercial (EP-001, EP-002), el carrito interactivo en localStorage
 * y la gestión de los 3 estados UI (Loading, Empty, Error).
 * Respeto estricto a AD-003, AD-005 y TaskSpec TS-FRONTEND-001.
 */

import { fetchProducts } from './api.js';
import { cartInstance } from './cart.js';

// ==============================================================================
// Utilidades de Formato
// ==============================================================================
export function formatCurrency(amount) {
  const numeric = typeof amount === 'number' ? amount : parseFloat(amount) || 0.0;
  return `$${numeric.toFixed(2).replace('.', ',')}`;
}

// ==============================================================================
// Referencias a Elementos del DOM
// ==============================================================================
const DOM = {
  // Búsqueda
  searchInput: document.getElementById('search-input'),
  clearSearchBtn: document.getElementById('clear-search-btn'),
  resetSearchBtn: document.getElementById('reset-search-btn'),

  // Estados UI
  loadingState: document.getElementById('loading-state'),
  emptyState: document.getElementById('empty-state'),
  errorState: document.getElementById('error-state'),
  errorMessage: document.getElementById('error-message'),
  retryBtn: document.getElementById('retry-btn'),

  // Catálogo
  catalogGrid: document.getElementById('catalog-grid'),

  // Carrito Drawer
  cartButton: document.getElementById('cart-button'),
  closeCartBtn: document.getElementById('close-cart-btn'),
  cartDrawer: document.getElementById('cart-drawer'),
  cartOverlay: document.getElementById('cart-overlay'),
  cartBadge: document.getElementById('cart-badge'),
  cartItems: document.getElementById('cart-items'),
  cartEmptyMessage: document.getElementById('cart-empty-message'),
  cartTotal: document.getElementById('cart-total'),
  clearCartBtn: document.getElementById('clear-cart-btn')
};

// Variable de debounce para búsqueda en tiempo real
let searchDebounceTimer = null;
let currentProducts = [];

// ==============================================================================
// Gestión de Estados UI (Loading, Empty, Error, Success)
// ==============================================================================
export function setUIState(state, message = '') {
  if (!DOM.loadingState || !DOM.emptyState || !DOM.errorState || !DOM.catalogGrid) {
    return;
  }

  DOM.loadingState.classList.add('hidden');
  DOM.emptyState.classList.add('hidden');
  DOM.errorState.classList.add('hidden');
  DOM.catalogGrid.classList.add('hidden');

  switch (state) {
    case 'loading':
      DOM.loadingState.classList.remove('hidden');
      break;
    case 'empty':
      DOM.emptyState.classList.remove('hidden');
      break;
    case 'error':
      DOM.errorState.classList.remove('hidden');
      if (DOM.errorMessage && message) {
        DOM.errorMessage.textContent = message;
      }
      break;
    case 'success':
      DOM.catalogGrid.classList.remove('hidden');
      break;
    default:
      DOM.catalogGrid.classList.remove('hidden');
      break;
  }
}

// ==============================================================================
// Renderizado del Catálogo de Productos (REQ-001, AC-001)
// ==============================================================================
export function renderCatalog(products) {
  if (!DOM.catalogGrid) return;
  DOM.catalogGrid.innerHTML = '';

  products.forEach(product => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.setAttribute('data-product-id', String(product.id));

    const title = document.createElement('h2');
    title.className = 'product-title';
    title.textContent = product.name;

    const desc = document.createElement('p');
    desc.className = 'product-description';
    desc.textContent = product.description || 'Sin descripción disponible.';

    const footer = document.createElement('div');
    footer.className = 'product-footer';

    const price = document.createElement('span');
    price.className = 'product-price';
    price.textContent = formatCurrency(product.price);

    const addBtn = document.createElement('button');
    addBtn.className = 'btn add-to-cart-btn';
    addBtn.textContent = 'Agregar al Carrito';
    addBtn.setAttribute('aria-label', `Agregar ${product.name} al carrito`);
    addBtn.addEventListener('click', () => {
      cartInstance.addItem(product, 1);
    });

    footer.appendChild(price);
    footer.appendChild(addBtn);

    card.appendChild(title);
    card.appendChild(desc);
    card.appendChild(footer);

    DOM.catalogGrid.appendChild(card);
  });
}

// ==============================================================================
// Renderizado del Carrito de Compras (DTO-CART-001, INV-002, INV-004)
// ==============================================================================
export function renderCart(cartState) {
  if (!DOM.cartBadge || !DOM.cartTotal || !DOM.cartItems) return;

  // Actualizar contador y total
  DOM.cartBadge.textContent = String(cartState.total_items);
  DOM.cartTotal.textContent = formatCurrency(cartState.total_amount);

  // Alternar mensaje de carrito vacío
  if (DOM.cartEmptyMessage) {
    if (cartState.items.length === 0) {
      DOM.cartEmptyMessage.classList.remove('hidden');
    } else {
      DOM.cartEmptyMessage.classList.add('hidden');
    }
  }

  DOM.cartItems.innerHTML = '';

  cartState.items.forEach(item => {
    const itemEl = document.createElement('div');
    itemEl.className = 'cart-item';
    itemEl.setAttribute('data-item-id', String(item.product_id));

    const info = document.createElement('div');
    info.className = 'item-info';

    const name = document.createElement('div');
    name.className = 'item-name';
    name.textContent = item.name;

    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.innerHTML = `${formatCurrency(item.unit_price)} × ${item.quantity} = <span class="item-subtotal">${formatCurrency(item.subtotal)}</span>`;

    info.appendChild(name);
    info.appendChild(meta);

    const controls = document.createElement('div');
    controls.className = 'item-controls';

    const decBtn = document.createElement('button');
    decBtn.className = 'btn-qty';
    decBtn.textContent = '−';
    decBtn.setAttribute('aria-label', `Disminuir cantidad de ${item.name}`);
    decBtn.addEventListener('click', () => {
      cartInstance.updateQuantity(item.product_id, -1);
    });

    const qtySpan = document.createElement('span');
    qtySpan.className = 'item-qty';
    qtySpan.textContent = String(item.quantity);

    const incBtn = document.createElement('button');
    incBtn.className = 'btn-qty';
    incBtn.textContent = '+';
    incBtn.setAttribute('aria-label', `Aumentar cantidad de ${item.name}`);
    incBtn.addEventListener('click', () => {
      cartInstance.updateQuantity(item.product_id, 1);
    });

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.textContent = '✕';
    removeBtn.setAttribute('aria-label', `Eliminar ${item.name} del carrito`);
    removeBtn.addEventListener('click', () => {
      cartInstance.removeItem(item.product_id);
    });

    controls.appendChild(decBtn);
    controls.appendChild(qtySpan);
    controls.appendChild(incBtn);
    controls.appendChild(removeBtn);

    itemEl.appendChild(info);
    itemEl.appendChild(controls);

    DOM.cartItems.appendChild(itemEl);
  });
}

// ==============================================================================
// Carga Asíncrona de Productos desde la API (EP-001)
// ==============================================================================
export async function loadCatalog(query = null) {
  setUIState('loading');
  try {
    const data = await fetchProducts(query);
    currentProducts = data.items;

    if (currentProducts.length === 0) {
      setUIState('empty');
    } else {
      renderCatalog(currentProducts);
      setUIState('success');
    }
  } catch (err) {
    const msg = err.message || 'No fue posible conectar con el servicio backend.';
    setUIState('error', msg);
  }
}

// ==============================================================================
// Control del Panel Lateral de Carrito (Drawer)
// ==============================================================================
export function openCartDrawer() {
  if (DOM.cartDrawer) {
    DOM.cartDrawer.classList.remove('hidden');
  }
}

export function closeCartDrawer() {
  if (DOM.cartDrawer) {
    DOM.cartDrawer.classList.add('hidden');
  }
}

// ==============================================================================
// Inicialización y Registro de Eventos del DOM
// ==============================================================================
export function initApp() {
  // Suscripción reactiva a cambios en el carrito
  cartInstance.subscribe(renderCart);
  renderCart(cartInstance.getState());

  // Apertura y cierre del carrito
  if (DOM.cartButton) {
    DOM.cartButton.addEventListener('click', openCartDrawer);
  }
  if (DOM.closeCartBtn) {
    DOM.closeCartBtn.addEventListener('click', closeCartDrawer);
  }
  if (DOM.cartOverlay) {
    DOM.cartOverlay.addEventListener('click', closeCartDrawer);
  }

  // Vaciar carrito
  if (DOM.clearCartBtn) {
    DOM.clearCartBtn.addEventListener('click', () => {
      cartInstance.clearCart();
    });
  }

  // Búsqueda con debounce (REQ-002, AC-002)
  if (DOM.searchInput) {
    DOM.searchInput.addEventListener('input', (e) => {
      const val = e.target.value;
      if (DOM.clearSearchBtn) {
        if (val.length > 0) {
          DOM.clearSearchBtn.classList.remove('hidden');
        } else {
          DOM.clearSearchBtn.classList.add('hidden');
        }
      }

      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        loadCatalog(val);
      }, 300);
    });
  }

  // Limpiar búsqueda
  if (DOM.clearSearchBtn) {
    DOM.clearSearchBtn.addEventListener('click', () => {
      if (DOM.searchInput) {
        DOM.searchInput.value = '';
      }
      DOM.clearSearchBtn.classList.add('hidden');
      loadCatalog('');
    });
  }

  if (DOM.resetSearchBtn) {
    DOM.resetSearchBtn.addEventListener('click', () => {
      if (DOM.searchInput) {
        DOM.searchInput.value = '';
      }
      if (DOM.clearSearchBtn) {
        DOM.clearSearchBtn.classList.add('hidden');
      }
      loadCatalog('');
    });
  }

  // Botón de reintento en caso de error
  if (DOM.retryBtn) {
    DOM.retryBtn.addEventListener('click', () => {
      const q = DOM.searchInput ? DOM.searchInput.value : null;
      loadCatalog(q);
    });
  }

  // Carga inicial del catálogo
  loadCatalog('');
}

// Inicializar cuando el DOM esté listo en ambiente navegador
if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  initApp();
} else if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', initApp);
}
