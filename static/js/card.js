const createCard = params => {
  if (params.kind == "t3" || params.kind == "t2") {
    // console.log(params);
    tag_html = "";
    for (tag in params.tags) {
      tag_html += `<li>${tag}</li>`;
    }
    return (result = `<div class="card post">
            <div class="image-container">
              <a href="${params.link_url}" target="_blank"><img src="${params.large_thumbnail}"/></a>
            </div>
            <div class="card-content">
              <a href="https://www.reddit.com${params.link_permalink}"
                ><h5 class="title">
                  ${params.link_title}
                </h5></a
              >
              <ul class="options">
                <li><a href="https://www.reddit.com${params.link_permalink}">Comments</a></li>
                <li><a href="https://www.reddit.com/r/${params.sub}">/r/${params.sub}</a></li>
              </ul>
              <ul class="tags">
                ${tag_html}
              </ul>
            </div>
          </div>`);
  } else {
    var md = window.markdownit();
    result = `<div class="card comment">
            <div class="card-content">
              <div class="comment-text">
                <a href="${params.link_permalink}"
                  ><h5 class="title">
                  ${params.link_title}
                  </h5></a
                >
                <p>
                ${params.body}
                </p>
              </div>
              <ul class="options">
              <li><a href="${params.link_permalink}${params.id}">Comments</a></li>
              <li><a href="https://www.reddit.com/r/${params.sub}">/r/${params.sub}</a></li>
              </ul>
              <ul class="tags">
                <li>Favorites</li>
                <li>Movies</li>
                <li>Books</li>
              </ul>
            </div>
          </div>`;
    return result;
  }
};

document.querySelectorAll(".next").forEach(nextButton => {
  nextButton.addEventListener("click", e => {
    e.preventDefault();
    const form = document.getElementById("search-form");
    const limit = form.elements["limit"].value;
    const save_type = form.elements["save-type"].value;
    const search = document.getElementById("search").value;
    const subreddit = document.getElementById("subreddit").value;

    const currentCount = parseInt(
      document.getElementById("currentCount").innerHTML
    );

    const totalCount = parseInt(
      document.getElementById("currentCount").innerHTML
    );

    if (currentCount >= totalCount) {
      e.target.style.visibility = "hidden";
    } else {
      document.getElementById("prev").style.visibility = "visible";
    }

    const user = document.getElementById("user").value;

    call_api(
      `/api/get_saved?user=${user}&limit=${limit}&save-type=${save_type}&search=${search}&subreddit=${subreddit}&offset=${currentCount}`
    );
  });
});

document.querySelectorAll(".prev").forEach(prevButton => {
  prevButton.addEventListener("click", e => {
    e.preventDefault();
    const form = document.getElementById("search-form");
    const limit = form.elements["limit"].value;
    const save_type = form.elements["save-type"].value;
    const search = document.getElementById("search").value;
    const subreddit = document.getElementById("subreddit").value;

    const currentCount = parseInt(
      document.getElementById("currentCount").innerHTML
    );

    const user = document.getElementById("user").value;

    call_api(
      `/api/get_saved?user=${user}&limit=${limit}&save-type=${save_type}&search=${search}&subreddit=${subreddit}&offset=${currentCount -
        limit}`
    );
  });
});

// const addButtons = (after, before) => {
//   next = after;
//   prev = before;
//   document.querySelectorAll(".next").forEach(nextButton => {
//     nextButton.style.visibility = next != null ? "visible" : "hidden";
//   });
//   document.querySelectorAll(".prev").forEach(prevButton => {
//     prevButton.style.visibility = prev != null ? "visible" : "hidden";
//   });
// };

const currentCountElem = document.getElementById("currentCount");
const totalCountElem = document.getElementById("totalCount");

const call_api = url => {
  console.log(url);
  fetch(url)
    .then(res => res.json())
    .then(res => {
      console.log(res);
      // const after = res["data"]["after"];
      // const before = res["data"]["before"];
      // addButtons(after, before);
      const count = res["count"];
      totalCount = count;

      res_count = res["children"].length;

      currentCount = res_count + parseInt(currentCountElem.innerHTML);

      currentCountElem.innerHTML = currentCount;
      totalCountElem.innerHTML = totalCount;

      if (totalCount > currentCount) {
        document
          .querySelectorAll(".next")
          .forEach(next => (next.style.visibility = "visible"));
      }

      return res["children"];
    })
    .then(res => {
      const cardContainer = document.querySelector(".cards-container");
      cardContainer.innerHTML = "";

      res.forEach(child => {
        // t3 = post, t2 = selftext, t1 = comment
        const kind = child["kind"];

        // meta_data
        const data = child;
        const link_permalink = data["link_permalink"];
        let id = data["name_id"];
        const link_url = data["link_url"];
        const user = data["author"];
        const sub = data["subreddit"];
        const link_title = data["link_title"];

        const is_self = data["is_self"];
        const selftext = data["selftext"];

        const thumbnail = data["thumbnail"];

        const tags = data["tags"];

        let large_thumbnail =
          "https://www.allaboutlean.com/wp-content/uploads/2018/10/Reddit-Logo-NOTEXT-2.png";
        if (data["preview"] != undefined) {
          let urls = data["preview"]["images"][0]["resolutions"];
          index = Math.min(urls.length - 1, 2);
          console.log(urls);
          large_thumbnail = urls[index]["url"];
        }
        const type = data["post_hint"];

        const body = data["body_html"];

        const params = {
          kind,
          data,
          link_permalink,
          link_url,
          user,
          sub,
          link_title,
          is_self,
          selftext,
          thumbnail,
          id,
          type,
          body,
          large_thumbnail,
          tags
        };
        cardContainer.insertAdjacentHTML("beforeend", createCard(params));
      });
    });
};

call_api(`/api/get_saved?user=${user}&limit=50`);

document.getElementById("submit").addEventListener("click", e => {
  e.preventDefault();
  const form = document.getElementById("search-form");
  const limit = form.elements["limit"].value;
  const save_type = form.elements["save-type"].value;
  const search = document.getElementById("search").value;
  const subreddit = document.getElementById("subreddit").value;
  const query = new URLSearchParams(new FormData(form)).toString();

  currentCountElem.innerHTML = 0;
  totalCountElem.innerHTML = 0;

  const user = document.getElementById("user").value;

  call_api(
    `/api/get_saved?user=${user}&limit=${limit}&save-type=${save_type}&search=${search}&subreddit=${subreddit}`
  );
});

document.getElementById("add-tag-button").addEventListener("click", e => {
  e.preventDefault();
  const tag = document.getElementById("tag-name").value;
  const data = `tag-name=${tag}`;
  console.log(data);
  fetch(`/api/add_tag`,{
    method:'POST',
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
  },
    body:data
  })
  .then(res=>console.log(res));
});

// const t = document.querySelectorAll(".card");
// t.forEach(target =>
//   target.addEventListener("mouseover", e => {
//     target.classList.add("wrap");
//   })
// );
// t.forEach(target =>
//   target.addEventListener("mouseleave", e => {
//     target.classList.remove("wrap");
//   })
// );
