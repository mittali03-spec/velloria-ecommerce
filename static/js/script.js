// =====================================================
// VELLORIA SHOPPING CART
// =====================================================


// ================= LOAD CART =================

let cart = JSON.parse(
    localStorage.getItem("velloriaCart")
) || [];


// ================= ADD TO CART =================

function addToCart(name, price) {

    // Make sure price is always a number
    price = Number(price);

    const existingProduct = cart.find(
        product => product.name === name
    );

    if (existingProduct) {

        existingProduct.quantity += 1;

    } else {

        cart.push({
            name: name,
            price: price,
            quantity: 1
        });

    }

    saveCart();
    updateCartCount();

    alert(name + " added to cart! 🛍️");
}


// ================= SAVE CART =================

function saveCart() {

    localStorage.setItem(
        "velloriaCart",
        JSON.stringify(cart)
    );

}


// ================= CART COUNT =================

function updateCartCount() {

    const cartCount =
        document.getElementById("cart-count");

    if (!cartCount) {
        return;
    }

    const totalItems = cart.reduce(
        (total, product) =>
            total + Number(product.quantity),
        0
    );

    cartCount.textContent = totalItems;

}


// ================= DISPLAY CART =================

function displayCart() {

    const cartItems =
        document.getElementById("cart-items");

    const emptyCart =
        document.getElementById("empty-cart");

    const cartSummary =
        document.getElementById("cart-summary");


    if (!cartItems) {
        return;
    }


    cartItems.innerHTML = "";


    // ================= EMPTY CART =================

    if (cart.length === 0) {

        if (emptyCart) {
            emptyCart.style.display = "block";
        }

        if (cartSummary) {
            cartSummary.style.display = "none";
        }

        updateTotal();

        return;
    }


    // ================= CART HAS PRODUCTS =================

    if (emptyCart) {
        emptyCart.style.display = "none";
    }

    if (cartSummary) {
        cartSummary.style.display = "block";
    }


    // ================= CREATE CART ITEMS =================

    cart.forEach((product, index) => {

        const item =
            document.createElement("div");

        item.className = "cart-item";


        const price =
            Number(product.price);

        const quantity =
            Number(product.quantity);


        item.innerHTML = `

            <div class="cart-item-info">

                <h3>
                    ${product.name}
                </h3>

                <p>
                    Velloria Collection
                </p>

                <div class="cart-item-price">
                    ₹${price.toLocaleString("en-IN")}
                </div>

            </div>


            <div class="quantity-controls">

                <button
                    onclick="changeQuantity(${index}, -1)"
                >
                    −
                </button>


                <span>
                    ${quantity}
                </span>


                <button
                    onclick="changeQuantity(${index}, 1)"
                >
                    +
                </button>


                <button
                    class="remove-button"
                    onclick="removeFromCart(${index})"
                >
                    Remove
                </button>

            </div>

        `;


        cartItems.appendChild(item);

    });


    // UPDATE TOTAL

    updateTotal();

}


// ================= CHANGE QUANTITY =================

function changeQuantity(index, change) {

    if (!cart[index]) {
        return;
    }


    cart[index].quantity =
        Number(cart[index].quantity) + change;


    if (cart[index].quantity <= 0) {

        cart.splice(index, 1);

    }


    saveCart();

    updateCartCount();

    displayCart();

}


// ================= REMOVE PRODUCT =================

function removeFromCart(index) {

    if (!cart[index]) {
        return;
    }


    cart.splice(index, 1);

    saveCart();

    updateCartCount();

    displayCart();

}


// ================= CALCULATE TOTAL =================

function updateTotal() {

    const totalElement =
        document.getElementById("cart-total");

    const subtotalElement =
        document.getElementById("cart-subtotal");


    // Calculate total safely

    let total = 0;


    cart.forEach(product => {

        const price =
            Number(product.price);

        const quantity =
            Number(product.quantity);


        total += price * quantity;

    });


    const formattedTotal =
        "₹" + total.toLocaleString("en-IN");


    // Update Total Amount

    if (totalElement) {

        totalElement.textContent =
            formattedTotal;

    }


    // Update Price

    if (subtotalElement) {

        subtotalElement.textContent =
            formattedTotal;

    }

}


// ================= CHECKOUT =================

function checkout() {

    if (cart.length === 0) {

        alert(
            "Your cart is empty. Add a product first! 🛍️"
        );

        return;
    }


    alert(
        "Proceeding to buy your Velloria items! 💳"
    );

}


// ================= PAGE LOAD =================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateCartCount();

        displayCart();

    }
);