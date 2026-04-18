#!/usr/bin/env bb
;; headlines-fetch.clj — Fetches geopol headlines via SearXNG, writes to headlines.json
;; Called every 30 min by OpenClaw cron job
;; v2: Smart social media filter, similarity dedup, clean timestamps

(require '[babashka.http-client :as http]
         '[cheshire.core :as json]
         '[clojure.java.io :as io]
         '[clojure.string :as str])

(def SEARXNG_URL (or (System/getenv "SEARXNG_URL") "http://localhost:8888"))
(def HEADLINES_FILE "/Users/claudius/clawd/frontion-site/headlines.json")
(def MAX_HEADLINES 200)
(def ist (java.time.ZoneId/of "Europe/Istanbul"))
(def dtf-id (java.time.format.DateTimeFormatter/ofPattern "yyyyMMdd-HHmmss"))
(def dtf-time (java.time.format.DateTimeFormatter/ofPattern "h:mm a"))
(def dtf-iso (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ssXXX"))

(def queries
  ["geopolitics war diplomacy"
   "Iran war US blockade Hormuz"
   "Ukraine Russia conflict"
   "Middle East ceasefire diplomacy"
   "US China trade summit"
   "NATO Europe defense"
   "energy oil gas crisis"
   "Turkey defense industry"])

;; ============ SEARCH ============

(defn searxng-search [query]
  (try
    (let [resp (http/get (str SEARXNG_URL "/search")
                         {:query-params {"q" query
                                         "format" "json"
                                         "category" "news"
                                         "time_range" "day"
                                         "language" "en"}
                          :timeout 30000})]
      (-> resp :body (json/decode true)))
    (catch Exception e
      (println (str "Search error for '" query "': " (.getMessage e)))
      nil)))

;; ============ SOURCE EXTRACTION ============

(defn extract-source [url]
  (let [known {"reuters" "Reuters" "apnews" "AP News" "bbc" "BBC"
               "aljazeera" "Al Jazeera" "cbsnews" "CBS News" "cnn" "CNN"
               "nytimes" "New York Times" "washingtonpost" "Washington Post"
               "ft.com" "Financial Times" "economist" "The Economist"
               "straitstimes" "Straits Times" "nikkei" "Nikkei Asia"
               "yahoo.com" "Yahoo News" "haaretz" "Haaretz"
               "firstpost" "Firstpost" "guardian" "The Guardian"
               "dw.com" "DW News" "france24" "France 24"
               "lemonde" "Le Monde" "atlanticcouncil" "Atlantic Council"
               "foreignpolicy" "Foreign Policy" "foreignaffairs" "Foreign Affairs"
               "thehill" "The Hill" "politico" "Politico" "axios" "Axios"
               "bloomberg" "Bloomberg" "wsj" "Wall Street Journal"
               "scmp" "SCMP" "al-monitor" "Al-Monitor"
               "jpost" "Jerusalem Post" "timesofisrael" "Times of Israel"
               "geopoliticalmonitor" "Geopolitical Monitor"
               "thediplomat" "The Diplomat" "middleeasteye" "Middle East Eye"
               "dailysabah" "Daily Sabah" "aa.com.tr" "Anadolu Agency"
               "telegraph.co.uk" "The Telegraph" "ndtv.com" "NDTV"
               "sky.com" "Sky News" "independent.co.uk" "The Independent"
               "time.com" "TIME" "newsweek" "Newsweek"
               "almasdronline" "Al Masdar" "trtworld" "TRT World"
               "middleeastmonitor" "Middle East Monitor"
               "iranintl" "Iran International" "iranwire" "Iran Wire"
               "israelhayom" "Israel Hayom" "ynetnews" "Ynet News"}
        matched (some (fn [[k v]] (when (str/includes? url k) v)) known)]
    (or matched
        (when-let [domain (second (re-find #"https?://(?:www\.)?([^/]+)" url))]
          (str/replace domain #"^www\." ""))
        "Unknown")))

;; ============ SMART SOCIAL MEDIA FILTER ============
;; Block generic social media, but allow official government/influential accounts

(def blocked-domains
  #{"google.com" "bing.com" "youtube.com" "facebook.com" "reddit.com"
    "tiktok.com" "instagram.com" "linkedin.com" "pinterest.com"
    "tumblr.com" "quora.com" "medium.com" "substack.com"})

(def allowed-official-accounts
  ;; Patterns for official government/influential accounts on social platforms
  [(re-pattern #"(?i)truthsocial\.com/.*/(?:trump|potus|whitehouse)")
   (re-pattern #"(?i)twitter\.com/(?:potus|whitehouse|statedept|deptofdefense|nato|trump)")
   (re-pattern #"(?i)x\.com/(?:potus|whitehouse|statedept|deptofdefense|nato|trump)")
   (re-pattern #"(?i)truthsocial\.com/.*/(?:trump)")
   (re-pattern #"(?i)threads\.net/(?:potus|whitehouse|trump)")])

(defn url-allowed? [url]
  (and (seq url)
       (let [domain (or (second (re-find #"https?://(?:www\.)?([^/]+)" url)) "")]
         (or
          ;; Allow if it matches an official account pattern
          (some (fn [pattern] (re-find pattern url)) allowed-official-accounts)
          ;; Otherwise block if domain is in blocked list
          (not (contains? blocked-domains domain))))))

;; ============ EMOJI & CATEGORY ============

(defn guess-emoji [title]
  (cond
    (re-find #"(?i)iran|tehran|hormuz|persian" title) "🇺🇸🇮🇷"
    (re-find #"(?i)ukrain|russia|kyiv|moscow|putin|zelensk" title) "🇺🇦"
    (re-find #"(?i)israel|hezbollah|lebanon|gaza|netanyahu|idf" title) "🇮🇱🇱🇧"
    (re-find #"(?i)china|beijing|xi |taiwan|pla" title) "🇺🇸🇨🇳"
    (re-find #"(?i)europe|nato|eu |german|france|merz|macron" title) "🇪🇺"
    (re-find #"(?i)pakistan|islamabad" title) "🇵🇰🇮🇷"
    (re-find #"(?i)turkey|turkiye|ankara|roketsan|erdogan" title) "🇹🇷"
    (re-find #"(?i)g7|g20|imf|economy|finance|inflation|gdp|market" title) "💰"
    (re-find #"(?i)drone|missile|weapon|military|defense|navy|army" title) "⚔️"
    (re-find #"(?i)oil|gas|energy|crude|lng|pipeline" title) "⛽"
    (re-find #"(?i)greenland|arctic|polar" title) "🇩🇰🧊"
    (re-find #"(?i)india|delhi|modi" title) "🇮🇳"
    (re-find #"(?i)south korea|japan|seoul|tokyo" title) "🇰🇷🇯🇵"
    (re-find #"(?i)trump|white house|congress|senate" title) "🇺🇸🏛️"
    (re-find #"(?i)ceasefire|peace|talks|diplomacy|deal|truce" title) "🕊️"
    :else "🌐"))

(defn guess-category [title]
  (cond
    (re-find #"(?i)iran|tehran|hormuz|persian" title) "US-Iran War"
    (re-find #"(?i)ukrain|russia|kyiv|moscow|putin|zelensk" title) "Ukraine-Russia War"
    (re-find #"(?i)israel|hezbollah|lebanon|gaza|idf" title) "Middle East"
    (re-find #"(?i)china|beijing|xi |taiwan" title) "US-China"
    (re-find #"(?i)ceasefire|peace|diplomacy|talks|truce|deal" title) "Diplomacy"
    (re-find #"(?i)g7|imf|economy|finance|inflation|gdp|market|trade" title) "Economy"
    (re-find #"(?i)oil|gas|energy|crude|lng|pipeline" title) "Energy"
    (re-find #"(?i)drone|missile|weapon|military|defense|navy" title) "Military"
    (re-find #"(?i)nato|europe|german|france|merz|macron" title) "Europe"
    (re-find #"(?i)turkey|turkiye|roketsan|erdogan" title) "Defense Industry"
    (re-find #"(?i)trump|white house|congress|senate|house" title) "US Politics"
    (re-find #"(?i)greenland|arctic" title) "Arctic"
    (re-find #"(?i)india|delhi|modi" title) "South Asia"
    (re-find #"(?i)south korea|japan|seoul|tokyo|korean" title) "Asia-Pacific"
    :else "Geopolitics"))

;; ============ SIMILARITY DEDUP ============
;; Remove stories that are too similar to each other
;; Uses word overlap on headlines — if 60%+ words overlap, it's a duplicate

(defn normalize-words [text]
  (-> text
      str/lower-case
      (str/replace #"[^\w\s]" "")
      (str/split #"\s+")
      set))

(defn word-overlap [a b]
  (let [wa (normalize-words a)
        wb (normalize-words b)
        intersection (count (clojure.set/intersection wa wb))
        union (count (clojure.set/union wa wb))]
    (if (zero? union) 0.0 (/ (double intersection) union))))

(def SIMILARITY_THRESHOLD 0.6)

;; Source authority ranking — higher = preferred when duplicates found
(def source-rank
  (zipmap ["Reuters" "AP News" "BBC" "Financial Times" "New York Times"
           "Washington Post" "The Economist" "Al Jazeera" "The Guardian"
           "DW News" "France 24" "Le Monde" "Bloomberg" "Wall Street Journal"
           "CBS News" "CNN" "The Telegraph" "Straits Times" "Nikkei Asia"
           "The Hill" "Politico" "Axios" "Atlantic Council" "Foreign Policy"
           "Foreign Affairs" "SCMP" "The Diplomat" "Haaretz"]
          (range 100 0 -3)))

(defn source-score [source]
  (get source-rank source 0))

(defn dedup-similar [headlines]
  (reduce
   (fn [kept h]
     (if (some (fn [existing]
                 (> (word-overlap (:headline h) (:headline existing))
                    SIMILARITY_THRESHOLD))
               kept)
       ;; Similar story already exists — keep whichever has higher source score
       (let [existing-idx (first (keep-indexed
                                   (fn [i e]
                                     (when (> (word-overlap (:headline h) (:headline e))
                                              SIMILARITY_THRESHOLD) i))
                                   kept))]
         (if existing-idx
           (let [existing-item (nth kept existing-idx)]
             (if (> (source-score (:source h)) (source-score (:source existing-item)))
               (assoc kept existing-idx h) ;; replace with better source
               kept)) ;; keep existing
           kept))
       (conj kept h)))
   []
   headlines))

;; ============ CONVERT ============

(defn result->headline [result]
  (let [url (:url result)
        title (str/trim (or (:title result) ""))
        snippet (or (:content result) "")]
    {:id (str "hl-" (.format (java.time.ZonedDateTime/now ist) dtf-id) "-" (Math/abs (hash url)))
     :timestamp (.format (java.time.ZonedDateTime/now ist) dtf-iso)
     :time (.format (java.time.ZonedDateTime/now ist) dtf-time)
     :emoji (guess-emoji title)
     :category (guess-category title)
     :headline title
     :summary (if (seq snippet) (subs (str/trim snippet) 0 (min (count (str/trim snippet)) 200)) "")
     :source (extract-source url)
     :url url}))

;; ============ MAIN ============

(defn load-existing []
  (if (.exists (io/file HEADLINES_FILE))
    (try
      (-> HEADLINES_FILE slurp (json/decode true))
      (catch Exception _ {:lastUpdated "" :headlines []}))
    {:lastUpdated "" :headlines []}))

(defn dedup-urls [existing new-stories]
  (let [existing-urls (set (map :url existing))]
    (remove #(contains? existing-urls (:url %)) new-stories)))

(defn -main []
  (println "Fetching geopol headlines...")
  (let [existing (load-existing)
        existing-headlines (or (:headlines existing) [])
        all-results (atom [])]

    (doseq [query queries]
      (println (str "  Searching: " query))
      (when-let [results (searxng-search query)]
        (doseq [r (:results results [])]
          (swap! all-results conj r)))
      (Thread/sleep 1500))

    (let [raw-new (->> @all-results
                       (map result->headline)
                       (filter #(and (url-allowed? (:url %))
                                    (seq (:headline %))))
                       (dedup-urls existing-headlines))
          deduped-new (dedup-similar (concat raw-new existing-headlines))
          ;; Take only new items from deduped result
          new-headlines (filter (fn [h] (some #(= (:url %) (:url h)) raw-new)) deduped-new)]

      (println (str "  Raw: " (count raw-new) ", After similarity dedup: " (count new-headlines)))

      (let [merged (->> (concat new-headlines existing-headlines)
                        (take MAX_HEADLINES))
            updated {:lastUpdated (.format (java.time.ZonedDateTime/now ist) dtf-iso)
                     :headlines (vec merged)}]

        (spit HEADLINES_FILE (json/encode updated {:pretty true}))
        (println (str "  Wrote " (count merged) " headlines to " HEADLINES_FILE))

        (let [git-dir (.getParent (io/file HEADLINES_FILE))]
          (try
            (when (.exists (io/file (str git-dir "/.git")))
              (println "  Committing to git...")
              (clojure.java.shell/sh "git" "add" "headlines.json" :dir git-dir)
              (clojure.java.shell/sh "git" "commit" "-m"
                (str "headlines update " (.format (java.time.ZonedDateTime/now ist) dtf-id))
                :dir git-dir)
              (clojure.java.shell/sh "git" "push" :dir git-dir)
              (println "  Pushed to GitHub."))
            (catch Exception e
              (println (str "  Git push skipped: " (.getMessage e))))))))))

(-main)