(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();


    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.sticky-top').addClass('shadow-sm').css('top', '0px');
        } else {
            $('.sticky-top').removeClass('shadow-sm').css('top', '-150px');
        }
    });


    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({ scrollTop: 0 }, 1500, 'easeInOutExpo');
        return false;
    });


    // Modal Video
    var $videoSrc;
    $('.btn-play').click(function () {
        $videoSrc = $(this).data("src");
    });
    console.log($videoSrc);
    $('#videoModal').on('shown.bs.modal', function (e) {
        $("#video").attr('src', $videoSrc + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0");
    })
    $('#videoModal').on('hide.bs.modal', function (e) {
        $("#video").attr('src', $videoSrc);
    })


    // Product carousel
    $(".product-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 25,
        loop: true,
        center: true,
        dots: false,
        nav: true,
        navText: [
            '<i class="bi bi-chevron-left"></i>',
            '<i class="bi bi-chevron-right"></i>'
        ],
        responsive: {
            0: {
                items: 1
            },
            576: {
                items: 1
            },
            768: {
                items: 2
            },
            992: {
                items: 3
            }
        }
    });


    // Testimonial carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        items: 1,
        loop: true,
        dots: true,
        nav: false,
    });

})(jQuery);

/* Notification */

function showNotificationBadge(newNotificationsCount) {
    const badge = document.getElementById("notificationBadge");
    if (newNotificationsCount > 0) {
        badge.style.display = "flex"; // הצגת העיגול האדום
        badge.textContent = newNotificationsCount; // הצגת מספר ההתראות
    } else {
        badge.style.display = "none"; // הסתרת העיגול האדום
    }
}


function toggleNotifications() {
    const modal = document.getElementById("notificationModal");
    const badge = document.getElementById("notificationBadge");

    if (modal.style.display === "none" || modal.style.display === "") {
        modal.style.display = "block";

        // הסתרת האייקון האדום (בזמן פתיחת ההתראות)
        badge.style.display = "none";

        // סימון התראות כנצפות בשרת
        fetch("/users/mark_notifications_seen", { method: "POST" })
            .catch(error => console.error("Error marking notifications as seen:", error));

        // טעינת התראות
        fetch("/users/get_notifications")
            .then(response => response.json())
            .then(data => {
                const notificationsList = document.getElementById("notifications-list");
                if (data.notifications.length > 0) {
                    notificationsList.innerHTML = data.notifications
                        .map(notification => `
                            <div class="notification-item">
                                <p><strong>תוכן:</strong> ${notification.content}</p>
                                <p><strong>מייל:</strong> ${notification.employee_email || "לא זמין"}</p>
                                <hr>
                            </div>
                        `)
                        .join("");
                } else {
                    notificationsList.innerHTML = "<p>אין התראות חדשות.</p>";
                }
            })
            .catch(error => console.error("Error fetching notifications:", error));
    } else {
        modal.style.display = "none";
    }
}

function closeNotifications() {
    const modal = document.getElementById("notificationModal");
    modal.style.display = "none";

    // הסרת המאזין
    document.removeEventListener("click", closeOnOutsideClick);
}

function closeOnOutsideClick(event) {
    const modal = document.getElementById("notificationModal");
    const notificationIcon = document.getElementById("notificationIcon");

    // בדיקה אם הלחיצה התבצעה מחוץ לחלון ומחוץ לאייקון
    if (!modal.contains(event.target) && event.target !== notificationIcon) {
        closeNotifications();
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    // טעינת התראות
    try {
        const notificationsResponse = await fetch("/users/get_notifications");
        const notificationsData = await notificationsResponse.json();

        showNotificationBadge(notificationsData.new_notifications_count); // עדכון העיגול האדום עם מספר ההתראות החדשות
    } catch (error) {
        console.error("Error fetching notifications:", error);
    }
});


/* Logout */

function logout() {
    fetch('/users/logout', {
        method: 'POST',
        credentials: 'same-origin'  // שולח את ה-cookies של ה-session
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;  // מפנה לדף הבית
        } else {
            showAlert('שגיאה במהלך הניתוק.');
        }
    }).catch(error => {
        console.error('שגיאה בלתי צפויה:', error);
    });
}

