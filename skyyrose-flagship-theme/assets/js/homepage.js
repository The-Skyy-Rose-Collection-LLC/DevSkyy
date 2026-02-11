        // Navbar scroll effect
        window.addEventListener('scroll', () => {
            const navbar = document.getElementById('navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });

        // Cart functionality
        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];
        
        function updateCartCount() {
            document.getElementById('cartCount').textContent = cart.length;
        }
        
        updateCartCount();

        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });

        // Collection cards hover animation already handled by CSS
        
        // Newsletter form
        document.querySelector('.newsletter-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const email = e.target.querySelector('input').value;
            alert(`Thank you for subscribing with ${email}! Welcome to the SkyyRose family.`);
            e.target.reset();
        });
