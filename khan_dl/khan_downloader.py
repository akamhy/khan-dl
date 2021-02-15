from bs4 import BeautifulSoup
import os
import re
import requests
import youtube_dl


class Khan_DL:
    def __init__(self, output_rel_path, course_root_url):
        self.course_root_url = course_root_url
        self.output_rel_path = os.getcwd() + "/" + output_rel_path

    def get_course_html(self):
        # Get Course Root Page HTML
        page_source = requests.get(self.course_root_url).text
        self.course_root_page_html = BeautifulSoup(page_source, "lxml")

    def generate_unit_slugs(self):
        """Generate Unit Header Slugs """

        self.unit_slugs = []
        self.unit_headers = []

        # Get The Course Name
        course_title = self.course_root_page_html.find(
            attrs={"data-test-id": "unit-block-title"}
        ).text

        # Extract Unit Headers for the course
        for units in self.course_root_page_html.find_all(
            attrs={"data-test-id": "unit-header"}
        ):
            self.unit_headers.append(units.text)

        # Builds Path Slugs at Unit Level
        counter = 0
        for headers in self.unit_headers:
            self.unit_slugs.append(course_title + "/" + str(counter) + "_" + headers)
            counter += 1

    def generate_unit_urls(self):
        """Generate Unit URLs """

        self.unit_urls = []
        # Extract Unit Page URLs for the course
        for urls in self.course_root_page_html.find_all(
            attrs={"data-test-id": "unit-header"}
        ):
            self.unit_urls.append(urls["href"])

    def generate_course_slugs_video_ids(self):
        self.youtube_id_list = []
        self.full_course_slugs = []
        for urls, slugs in zip(self.unit_urls, self.unit_slugs):
            unit_page_source = requests.get("https://www.khanacademy.org" + urls).text
            self.unit_page_html = BeautifulSoup(unit_page_source, "lxml")
            unit_counter = 0

            # Collect Youtube Ids from Sub Unit Page HTML list
            current_youtube_id_list = re.findall(
                r"\"youtubeId\":\"[A-Za-z0-9.\-_]{11}\"", str(self.unit_page_html)
            )
            current_youtube_id_list = list(dict.fromkeys(current_youtube_id_list))

            # Genearate Full Course Slugs and Relative Youtube Ids List
            for current_youtube_id, unit_sub_heads, unit_sub_head_body in zip(
                current_youtube_id_list,
                self.unit_page_html.find_all(
                    attrs={"data-test-id": "lesson-card-link"}
                ),
                self.unit_page_html.find_all("div", class_="_1o51yl6"),
            ):

                # Append Youtube ids to the List
                self.youtube_id_list.append(current_youtube_id[13:24])
                video_counter = 0

                # Find Individual Video Blocks and Validate whether it is video
                # or not  - Classes vary dep. on Page
                for unit_sub_head_div in unit_sub_head_body.find_all(
                    "div", {"class": ["_10ct3cvu", "_1p9458yw"]}
                ):
                    aria_label_html = unit_sub_head_div.find_all(
                        "span", class_="_e296pg"
                    )
                    aria_label = aria_label_html[0]["aria-label"]

                    # Check whether it  is a video or not
                    if aria_label == "Video":
                        video_topic = unit_sub_head_div.find("span", class_="_14hvi6g8")

                        self.full_course_slugs.append(
                            self.output_rel_path
                            + "/"
                            + slugs
                            + "/"
                            + str(unit_counter)
                            + "_"
                            + unit_sub_heads.text
                            + "/"
                            + str(video_counter)
                            + "_"
                            + video_topic.text
                            + ".mp4"
                        )

                    video_counter += 1
                unit_counter += 1

    def download_videos(self):
        print("\nDownloading Videos....\n")
        for output_file, video_id in zip(self.full_course_slugs, self.youtube_id_list):
            youtube_url = "https://www.youtube.com/watch?v=" + video_id
            with youtube_dl.YoutubeDL({"outtmpl": output_file}) as ydl:
                ydl.download([youtube_url])
