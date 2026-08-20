async function addToCart(productId) {

    try {

        const response = await fetch(
            "/api/cart/add",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    product_id: productId
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            alert(
                data.error || "Unable to add product."
            );

            return;
        }


        updateCartCount(
            data.cart_count
        );


        showNotification(
            "Product added to cart!"
        );


    } catch (error) {

        console.error(error);

        alert(
            "Something went wrong."
        );
    }
}


async function removeFromCart(productId) {

    try {

        const response = await fetch(
            `/api/cart/remove/${productId}`,
            {
                method: "DELETE"
            }
        );


        const data = await response.json();


        if (!response.ok) {

            alert(
                data.error ||
                "Unable to remove product."
            );

            return;
        }


        updateCartCount(
            data.cart_count
        );


        window.location.reload();


    } catch (error) {

        console.error(error);

        alert(
            "Something went wrong."
        );
    }
}


function updateCartCount(count) {

    const cartCount =
        document.getElementById(
            "cart-count"
        );


    if (cartCount) {

        cartCount.textContent = count;

    }
}


function showNotification(message) {

    const notification =
        document.createElement("div");


    notification.className =
        "notification";


    notification.textContent =
        message;


    document.body.appendChild(
        notification
    );


    setTimeout(() => {

        notification.remove();

    }, 2500);
}