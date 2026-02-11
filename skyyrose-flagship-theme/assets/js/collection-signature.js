        // Products Data
        const products = [
            { id: 'sig1', name: 'Foundation Blazer', price: 495, badge: 'Flagship', image: '🧥' },
            { id: 'sig2', name: 'Essential Trouser', price: 295, badge: null, image: '👖' },
            { id: 'sig3', name: 'Luxury Logo Tee', price: 125, badge: 'Bestseller', image: '👕' },
            { id: 'sig4', name: 'Heritage Overcoat', price: 595, badge: 'Limited', image: '🧥' },
            { id: 'sig5', name: 'Classic Oxford Shirt', price: 185, badge: null, image: '👔' },
            { id: 'sig6', name: 'Premium Knit Polo', price: 165, badge: 'New', image: '👕' },
            { id: 'sig7', name: 'Signature Cashmere Sweater', price: 385, badge: null, image: '🧶' },
            { id: 'sig8', name: 'Executive Leather Belt', price: 145, badge: null, image: '〰️' }
        ];

        // Render Products
        function renderProducts() {
            const grid = document.getElementById('productsGrid');
            grid.innerHTML = products.map(p => `
                <div class="product-card">
                    <div class="product-image">
                        ${p.badge ? `<span class="product-badge">${p.badge}</span>` : ''}
                        <button class="quick-add" onclick="addToCart('${p.id}', '${p.name}', ${p.price})">Quick Add</button>
                    </div>
                    <div class="product-info">
                        <h3 class="product-name"><a href="single-product.html?id=${p.id}&collection=signature">${p.name}</a></h3>
                        <p class="product-price">$${p.price}</p>
                    </div>
                </div>
            `).join('');
        }

        // Cart Functions
        function getCart() {
            return JSON.parse(localStorage.getItem('skyyrose_cart') || '[]');
        }

        function saveCart(cart) {
            localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
            updateCartCount();
        }

        function addToCart(id, name, price) {
            const cart = getCart();
            const existing = cart.find(item => item.id === id);
            if (existing) {
                existing.quantity++;
            } else {
                cart.push({ id, name, price, quantity: 1, collection: 'signature' });
            }
            saveCart(cart);
            showNotification(`${name} added to cart`);
        }

        function updateCartCount() {
            const cart = getCart();
            const count = cart.reduce((sum, item) => sum + item.quantity, 0);
            document.getElementById('cartCount').textContent = count;
        }

        function showNotification(message) {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; bottom: 2rem; right: 2rem;
                background: var(--signature-gold); color: var(--bg-dark);
                padding: 1rem 2rem; border-radius: 4px;
                z-index: 10000; animation: slideIn 0.3s ease;
                font-weight: 600;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }

        // Navbar Scroll Effect
        window.addEventListener('scroll', () => {
            const navbar = document.getElementById('navbar');
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        });

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderProducts();
            updateCartCount();
        });
