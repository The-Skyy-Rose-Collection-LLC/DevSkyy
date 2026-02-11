        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];
        let wishlist = JSON.parse(localStorage.getItem('skyyrose_wishlist')) || [];

        function updateCartCount() {
            document.getElementById('cartCount').textContent = cart.reduce((sum, item) => sum + item.qty, 0);
        }
        updateCartCount();

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Add to cart
        document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = btn.closest('.product-card');
                const item = {
                    id: card.dataset.id,
                    name: card.dataset.name,
                    collection: card.dataset.collection,
                    price: parseInt(card.dataset.price),
                    size: 'M',
                    color: 'Default',
                    qty: 1
                };

                const existing = cart.findIndex(i => i.id === item.id);
                if (existing > -1) {
                    cart[existing].qty++;
                } else {
                    cart.push(item);
                }

                localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
                updateCartCount();

                const toast = document.getElementById('toast');
                toast.textContent = `${item.name} added to cart!`;
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 3000);
            });
        });

        // Add to wishlist
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = btn.closest('.product-card');
                const item = {
                    id: card.dataset.id,
                    name: card.dataset.name,
                    collection: card.dataset.collection,
                    price: parseInt(card.dataset.price)
                };

                if (!wishlist.find(i => i.id === item.id)) {
                    wishlist.push(item);
                    localStorage.setItem('skyyrose_wishlist', JSON.stringify(wishlist));
                    btn.textContent = '❤️';
                    
                    const toast = document.getElementById('toast');
                    toast.textContent = `${item.name} added to wishlist!`;
                    toast.classList.add('show');
                    setTimeout(() => toast.classList.remove('show'), 3000);
                }
            });
        });

        // Check if items are already in wishlist
        wishlist.forEach(item => {
            const card = document.querySelector(`[data-id="${item.id}"]`);
            if (card) {
                card.querySelector('.wishlist-btn').textContent = '❤️';
            }
        });
