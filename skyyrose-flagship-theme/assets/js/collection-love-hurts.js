        // Products Data
        const products = [
            { id: 'lh1', name: 'Heartbreak Hoodie', price: 185, originalPrice: null, badge: 'Bestseller', image: '💔' },
            { id: 'lh2', name: 'Tears Bomber Jacket', price: 325, originalPrice: null, badge: 'New', image: '🧥' },
            { id: 'lh3', name: 'Wounded Heart Tee', price: 85, originalPrice: null, badge: null, image: '👕' },
            { id: 'lh4', name: 'Scar Cargo Pants', price: 195, originalPrice: 245, badge: 'Sale', image: '👖' },
            { id: 'lh5', name: 'Emotion Knit Sweater', price: 225, originalPrice: null, badge: null, image: '🧶' },
            { id: 'lh6', name: 'Resilience Denim Jacket', price: 285, originalPrice: null, badge: 'Limited', image: '🧥' }
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
                        <h3 class="product-name"><a href="single-product.html?id=${p.id}&collection=love-hurts">${p.name}</a></h3>
                        <p class="product-price">
                            $${p.price}
                            ${p.originalPrice ? `<span class="product-original-price">$${p.originalPrice}</span>` : ''}
                        </p>
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
                cart.push({ id, name, price, quantity: 1, collection: 'love-hurts' });
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
                background: var(--love-hurts); color: #fff;
                padding: 1rem 2rem; border-radius: 4px;
                z-index: 10000; animation: slideIn 0.3s ease;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }

        // Floating Hearts
        function createFloatingHearts() {
            const container = document.getElementById('floatingHearts');
            for (let i = 0; i < 15; i++) {
                const heart = document.createElement('div');
                heart.className = 'heart';
                heart.textContent = '♥';
                heart.style.left = Math.random() * 100 + '%';
                heart.style.animationDelay = Math.random() * 20 + 's';
                heart.style.fontSize = (Math.random() * 1 + 1) + 'rem';
                container.appendChild(heart);
            }
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
            createFloatingHearts();
        });
