/**
 * Cliente de Transporte HTTP de Solo Lectura para Catálogo Comercial (EP-001, EP-002).
 * Consume la API REST de FastAPI sin mutaciones y con manejo estructurado de errores (DTO-ERR-001).
 * Respeto estricto a AD-003, AD-005 y TaskSpec TS-FRONTEND-001.
 */

export class ApiError extends Error {
  constructor(message, status = 500, errorCode = 'API_ERROR') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
  }
}

export const API_BASE_URL = (typeof window !== 'undefined' && window.API_BASE_URL)
  ? window.API_BASE_URL
  : 'http://127.0.0.1:8000/api/v1';

/**
 * Consulta la lista de productos disponibles en el catálogo comercial (EP-001).
 * Soporta filtro opcional por término de búsqueda insensible a mayúsculas/minúsculas.
 * @param {string|null} searchTerm - Término de búsqueda (q)
 * @returns {Promise<{items: Array<{id: number, name: string, description: string|null, price: number}>, total: number}>}
 */
export async function fetchProducts(searchTerm = null) {
  let url = `${API_BASE_URL}/products`;
  if (searchTerm && typeof searchTerm === 'string' && searchTerm.trim().length > 0) {
    const encoded = encodeURIComponent(searchTerm.trim());
    url += `?q=${encoded}`;
  }

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      let errorDetail = 'Error al consultar productos';
      let errorCode = 'CATALOG_FETCH_ERROR';
      try {
        const errorBody = await response.json();
        if (errorBody && errorBody.detail) {
          errorDetail = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
        }
        if (errorBody && errorBody.error_code) {
          errorCode = errorBody.error_code;
        }
      } catch {
        // Fallback a texto o status
      }
      throw new ApiError(errorDetail, response.status, errorCode);
    }

    const data = await response.json();
    return {
      items: Array.isArray(data.items) ? data.items : [],
      total: typeof data.total === 'number' ? data.total : (data.items ? data.items.length : 0)
    };
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Error de conexión con el servicio de catálogo', 0, 'NETWORK_ERROR');
  }
}

/**
 * Consulta el detalle de un producto específico por su identificador único (EP-002).
 * @param {number|string} productId - Identificador único del producto
 * @returns {Promise<{id: number, name: string, description: string|null, price: number}>}
 */
export async function fetchProductById(productId) {
  if (productId === undefined || productId === null) {
    throw new ApiError('Identificador de producto requerido', 400, 'INVALID_ID');
  }

  const url = `${API_BASE_URL}/products/${encodeURIComponent(productId)}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      let errorDetail = `Producto #${productId} no encontrado`;
      let errorCode = 'PRODUCT_NOT_FOUND';
      try {
        const errorBody = await response.json();
        if (errorBody && errorBody.detail) {
          errorDetail = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
        }
        if (errorBody && errorBody.error_code) {
          errorCode = errorBody.error_code;
        }
      } catch {
        // Fallback a mensaje por defecto
      }
      throw new ApiError(errorDetail, response.status, errorCode);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Error de conexión al obtener producto', 0, 'NETWORK_ERROR');
  }
}
