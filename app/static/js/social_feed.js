//social_feed
$(document).ready(function () {
    function formatDateTime(input) {
        const date = new Date(input);
        if (isNaN(date)) return input;

        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = String(date.getFullYear()).slice(2);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return `${hours}:${minutes} ${day}/${month}/${year}`;
    }

    function fetchPosts() {

        const loggedInUserEmail = $("#postsContainer").data("user-email"); // קבלת המייל של המשתמש המחובר

        $.get("/posts/", function (data) {
            $("#postsContainer").empty();
            data.forEach(post => {
                let isUserPost = post.publisher_email === loggedInUserEmail;

                let sortedComments = post.comments
                    .slice()
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

                let commentsHtml = sortedComments.slice(0, 2)
                    .map(comment => {
                        let isUserComment = comment.commenter_email === loggedInUserEmail;
                        return `
                        <div class="comment" data-comment-id="${comment.id}" data-post-id="${post.id}">
                            ${isUserComment ? '<button class="delete-comment-btn" data-comment-id="' + comment.id + '" data-post-id="' + post.id + '">X</button>' : ""}
                            <span class="comment-date">${formatDateTime(comment.created_at)}</span>
                            <strong class="commenter-name user-info" data-email="${comment.commenter_email}" style="cursor:pointer;">
                                ${comment.commenter_name}
                            </strong>
                            <p class="comment-content">${comment.content}</p>
                        </div>
                    `;
                    }).join("");

                let hiddenCommentsHtml = sortedComments.slice(2).map(comment => {
                    let isUserComment = comment.commenter_email === loggedInUserEmail;
                    return `
                    <div class="comment" data-comment-id="${comment.id}" data-post-id="${post.id}">
                        ${isUserComment ? '<button class="delete-comment-btn" data-comment-id="' + comment.id + '" data-post-id="' + post.id + '">X</button>' : ""}
                        <span class="comment-date">${comment.created_at}</span>
                        <strong class="commenter-name user-info" data-email="${comment.commenter_email}" style="cursor:pointer;">
                            ${comment.commenter_name}
                        </strong>
                        <p class="comment-content">${comment.content}</p>
                    </div>
                `;
                }).join("");

                let postElement = `
                <div class="post-card" data-post-id="${post.id}">
                    ${isUserPost ? '<button class="delete-post-btn">X</button>' : ""}
                    <div class="post-header">
                        <h5 class="post-author user-info" data-email="${post.publisher_email}" style="cursor:pointer;">
                            ${post.publisher_name}
                        </h5>
                        <span class="post-date">${formatDateTime(post.created_at)}</span>
                    </div>
                    <p class="post-content">${post.content}</p>
                    <button class="btn btn-link toggle-comment">תגובה</button>
                    <div class="comment-box">
                        <input type="text" class="form-control comment-input" placeholder="כתוב תגובה...">
                        <button class="btn btn-primary mt-2 submit-comment">שלח</button>
                    </div>
    
                    <div class="comments-list">
                        ${commentsHtml}
                        <div class="hidden-comments" style="display: none;">
                            ${hiddenCommentsHtml}
                        </div>
                        ${post.comments.length > 2 ? `<button class="btn btn-link show-more-comments">ראה עוד</button>` : ""}
                    </div>
                </div>`;

                $("#postsContainer").append(postElement);
            });
        });
    }
    fetchPosts();

    $(document).on("click", ".commenter-name", function () {
        let userEmail = $(this).attr("data-email");
        if (!userEmail || userEmail === "undefined") {
            return;
        }

        $.get(`/users/info/${userEmail}`, function (user) {
            let roleText = user.role === "manager" || user.role === "co_manager" ? "בעל משק חקלאי" :
                user.role === "job_seeker" ? "מתנדב/מחפש עבודה" : "משתמש רגיל";

            let locationText = user.role === "manager" || user.role === "co_manager" ? `<p><strong>מקום המשק:</strong> ${user.location}</p>` : "";

            let userInfoHtml = `
                <div class="user-popup">
                    <h4>${user.first_name} ${user.last_name}</h4>
                    <p><strong>תפקיד:</strong> ${roleText}</p>
                    ${locationText}
                </div>
            `;

            $("#userInfoModal .modal-body").html(userInfoHtml);
            $("#userInfoModal").modal("show");
        }).fail(function () {
            console.error("⚠️ שגיאה בשליפת פרטי המשתמש.");
        });
    });

    $(document).on("click", ".user-info", function () {
        let userEmail = $(this).data("email");

        $.get(`/users/info/${userEmail}`, function (user) {
            let roleText = "משתמש רגיל";
            if (user.role === "manager" || user.role === "co_manager") {
                roleText = "בעל משק חקלאי";
            } else if (user.role === "job_seeker") {
                roleText = "מתנדב/מחפש עבודה";
            }

            let locationText = user.role === "manager" || user.role === "co_manager" ? `<p><strong>מקום המשק:</strong> ${user.location}</p>` : "";

            let userInfoHtml = `
            <div class="user-popup">
                <h4>${user.first_name} ${user.last_name}</h4>
                <hr class="section-divider">

                <p><strong>תפקיד:</strong> ${roleText}</p>
                ${locationText}
            </div>
        `;

            $("#userInfoModal .modal-body").html(userInfoHtml);
            $("#userInfoModal").modal("show");
        });
    });

    $(document).on("click", ".delete-comment-btn", function () {
        let commentId = $(this).data("comment-id");
        let postId = $(this).data("post-id");

        if (!commentId || !postId) {
            console.error("⚠️ חסר ID של התגובה או הפוסט.");
            return;
        }

        $("#alertTitle").text("אישור מחיקה");
        $("#alertMessage").text("אתה בטוח שברצונך למחוק את התגובה?");
        $("#customAlert").fadeIn();

        $(".alert-close").off("click").on("click", function () {
            $("#customAlert").fadeOut();
        });

        $("#alertConfirm").off("click").on("click", function () {
            $.ajax({
                url: `/posts/${postId}/comments/${commentId}`,
                type: "DELETE",
                success: function () {
                    fetchPosts();
                    $("#customAlert").fadeOut();
                },
                error: function () {
                    $("#alertTitle").text("שגיאה");
                    $("#alertMessage").text("אירעה שגיאה בעת מחיקת התגובה.");
                }
            });
        });
    });


    $(document).on("click", ".delete-post-btn", function () {
        let postElement = $(this).closest(".post-card");
        let postId = postElement.attr("data-post-id");

        $("#alertTitle").text("אישור מחיקה");
        $("#alertMessage").text("אתה בטוח שברצונך למחוק את הפוסט?");
        $("#customAlert").fadeIn();

        $(".alert-close").off("click").on("click", function () {
            $("#customAlert").fadeOut();
        });

        $("#alertConfirm").off("click").on("click", function () {
            $.ajax({
                url: `/posts/${postId}`,
                type: "DELETE",
                success: function () {
                    fetchPosts();
                    $("#customAlert").fadeOut();
                },
                error: function () {
                    $("#alertTitle").text("שגיאה");
                    $("#alertMessage").text("אירעה שגיאה בעת מחיקת הפוסט.");
                }
            });
        });
    });


    // publish post 
    $("#newPostForm").submit(function (event) {
        event.preventDefault();
        let content = $("#newPostContent").val().trim();
        if (!content) {
            showAlert("לא ניתן לפרסם פוסט ריק!");
            return;
        }

        $.ajax({
            url: "/posts/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ "content": content }),
            success: function () {
                $("#newPostContent").val("");
                fetchPosts();
            },
            error: function () {
                showAlert("שגיאה בשליחת הפוסט.");
            }
        });
    });

    // comments - open/close
    $(document).on("click", ".toggle-comment", function () {
        $(this).siblings(".comment-box").toggle();
    });

    //publish comments
    $(document).on("click", ".submit-comment", function () {
        let postElement = $(this).closest(".post-card");
        let postId = postElement.attr("data-post-id");
        let commentContent = postElement.find(".comment-input").val().trim();

        if (!commentContent) {
            showAlert("לא ניתן לשלוח תגובה ריקה!");
            return;
        }

        $.ajax({
            url: "/posts/comments",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                "post_id": postId,
                "content": commentContent
            }),
            success: function () {
                postElement.find(".comment-input").val("");
                fetchPosts();
            },
            error: function () {
                showAlert("שגיאה בשליחת התגובה.");
            }
        });
    });

    $(document).on("click", ".show-more-comments", function () {
        let postElement = $(this).closest(".post-card");
        let hiddenComments = postElement.find(".hidden-comments");

        hiddenComments.slideDown();
        $(this).remove();
    });

});
$(document).on("click", ".delete-comment-btn", function () {
    let commentId = $(this).data("comment-id");
    let postId = $(this).data("post-id");

    if (!commentId || !postId) {
        console.error("חסר ID של התגובה או הפוסט.");
        return;
    }

    $("#alertTitle").text("אישור מחיקה");
    $("#alertMessage").text("אתה בטוח שברצונך למחוק את התגובה?");
    $("#customAlert").fadeIn();

    $(".alert-close").off("click").on("click", function () {
        $("#customAlert").fadeOut();
    });

    $("#alertConfirm").off("click").on("click", function () {
        $.ajax({
            url: `/posts/${postId}/comments/${commentId}`,
            type: "DELETE",
            success: function () {
                fetchPosts();
                $("#customAlert").fadeOut();
            },
            error: function () {
                $("#alertTitle").text("שגיאה");
                $("#alertMessage").text("אירעה שגיאה בעת מחיקת התגובה.");
            }
        });
    });
});
