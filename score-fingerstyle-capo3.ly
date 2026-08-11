\version "2.24.3"

\paper {
  property-defaults.fonts.serif = "D2Coding"
  property-defaults.fonts.sans = "D2Coding"
  top-margin = 12\mm
  bottom-margin = 12\mm
  left-margin = 13\mm
  right-margin = 13\mm
}

\header {
  title = "나의 어릴 적 이야기"
  subtitle = "산들 — 핑거스타일 편곡"
  instrument = "Capo 3fret (실음 F키 · −2키) · 프렛 번호는 카포 기준"
  tagline = ##f
}

%%% ---------- 반주 셀 정의 (2박 아르페지오) ----------

vmOne = {
  d8 a d' fis' cis8 e a cis' |
  b,8 fis b d' a,8 fis a cis' |
  g,8 d g b d8 a d' fis' |
  e,8 b, g b <a, g d'>4 <a, g cis'>4 |
}

vmTwo = {
  g,8 d g b d8 a d' fis' |
  cis8 e a cis' b,8 fis b d' |
  a,8 d fis a g,8 d g b |
  a,8 e a cis' d8 a d' fis' |
}

vmThree = {
  d8 a d' fis' cis8 e a cis' |
  b,8 fis b d' a,8 d fis a |
  g,8 d g b d8 a d' fis' |
  e,8 b, g b <a, g d'>4 <a, g cis'>4 |
}

vmFour = {
  g,8 d g b d8 a d' fis' |
  cis8 e a cis' b,8 fis b d' |
  a,8 d fis a g,8 d g b |
  a,8 e a cis' d8 a c' fis' |
}

cmOne = {
  g,8 d g b a,8 e a cis' |
  b,8 fis b d' a,8 fis a cis' |
  e,8 b, g b a,8 e a cis' |
  d8 a d' fis' d8 a c' fis' |
}

cmTwo = {
  g,8 d g b a,8 e a cis' |
  ais,8 e g cis' b,8 fis b d' |
  a,8 fis a cis' e,8 b, g b |
  a,8 e g d' a,8 e g cis' |
}

cmTwoB = {
  g,8 d g b a,8 e a cis' |
  ais,8 e g cis' b,8 fis b d' |
  a,8 fis a cis' gis,8 d f b |
  e,8 b, g b <a, g d'>4 <a, g cis'>4 |
}

cmFourSus = {
  g,8 d g b d8 a d' fis' |
  cis8 e a cis' b,8 fis b d' |
  a,8 d fis a g,8 d g b |
  <a, e a cis'>4 <d a d' fis'>4 <d a d' g'>4 <d a d' fis'>4 |
}

%%% ---------- 인트로 (멜로디+베이스 2성부) ----------

introMusic = {
  << { d'2 b8 d'8 e'8 d'8 }
     \\ { g,8 g d g r2 } >> |
  << { cis'4 e'4 e'4 fis'4 }
     \\ { a,2 ais,2 } >> |
  << { fis'1 }
     \\ { b,2 a,4 gis,4 } >> |
  << { d'8\2\glissando e'8\2 e'8\2\glissando fis'8\2 fis'8\2 e'8\2 d'4\2 }
     \\ { e,2 e,2 } >> |
  << { d'8\2\glissando e'8\2 d'2.\2 }
     \\ { a,2 a,2 } >> |
}

introChords = \chordmode {
  g1 |
  a2 ais2:dim7 |
  b2:m fis4:m/a gis4:m7.5- |
  e1:m |
  a1:7 |
}

%%% ---------- 엔딩 ----------

endingMusic = {
  g,8 d g b a,8 e a cis' |
  d8 a d' fis' <d a d' g'>4 <d a d' fis'>4 |
  g,8 d g b a,4 e'8\2\glissando fis'8\2 |
}

endingChords = \chordmode {
  g2 a2 |
  d2 d4:sus4 d4 |
  g2 a2:7 |
}

%%% ---------- 아웃트로 (솔로+베이스 2성부) ----------

outroMusic = {
  << { fis'2\2 e'8\2\glissando fis'8\2 fis'4\2 }
     \\ { d2 cis2 } >> |
  << { d'8\2\glissando e'8\2 e'2.\2 }
     \\ { b,2 a,2 } >> |
  << { d'4^\markup \italic "rit." b4 cis'2 }
     \\ { g,2 a,2 } >> |
  <d a d' fis'>1\fermata |
}

outroChords = \chordmode {
  d2 a2/cis |
  b2:m d2/a |
  g2 a2:7 |
  d1 |
}

%%% ---------- 코드 라인 ----------

vcOne = \chordmode {
  d2 a2/cis | b2:m fis2:m/a | g2 d2 | e2:m a4:7sus4 a4:7 |
}
vcTwo = \chordmode {
  g2 d2 | a2/cis b2:m | d2/a g2 | a2 d2 |
}
vcThree = \chordmode {
  d2 a2/cis | b2:m d2/a | g2 d2 | e2:m a4:7sus4 a4:7 |
}
vcFour = \chordmode {
  g2 d2 | a2/cis b2:m | d2/a g2 | a2 d4 d4:7 |
}
ccOne = \chordmode {
  g2 a2 | b2:m fis2:m/a | e2:m a2 | d2 d2:7 |
}
ccTwo = \chordmode {
  g2 a2 | ais2:dim7 b2:m | fis2:m/a e2:m | a2:7sus4 a2:7 |
}
ccTwoB = \chordmode {
  g2 a2 | ais2:dim7 b2:m | fis2:m/a gis2:dim7 | e2:m a4:7sus4 a4:7 |
}
ccFourSus = \chordmode {
  g2 d2 | a2/cis b2:m | d2/a g2 | a4 d4 d4:sus4 d4 |
}

%%% ---------- 전체 조립 ----------

music = {
  \key d \major
  \time 4/4
  \tempo 4 = 66
  \mark \markup \box "Intro"
  \introMusic
  \mark \markup \box "1절"
  \vmOne \vmTwo \vmThree \vmFour
  \mark \markup \box "후렴"
  \cmOne \cmTwo \vmOne \cmFourSus
  \mark \markup \box "간주"
  \vmThree \cmFourSus
  \mark \markup \box "2절"
  \vmThree \vmFour
  \mark \markup \box "후렴"
  \cmOne \cmTwoB \vmOne \cmFourSus
  \mark \markup \box "엔딩"
  \endingMusic
  \mark \markup \box "Outro"
  \outroMusic
  \bar "|."
}

allChords = {
  \introChords
  \vcOne \vcTwo \vcThree \vcFour
  \ccOne \ccTwo \vcOne \ccFourSus
  \vcThree \ccFourSus
  \vcThree \vcFour
  \ccOne \ccTwoB \vcOne \ccFourSus
  \endingChords
  \outroChords
}

%%% ---------- 가사 (박자 지정 독립 라인) ----------

allLyrics = \lyricmode {
  % 인트로 (m1-5) — m5 끝에 "어느" 픽업
  \skip 1 \skip 1 \skip 1 \skip 1
  \skip 2. 어8 -- 느8
  % 1절 (m6-21)
  날4 갑8 -- 자8 -- 기4 생8 -- 각8
  나2 내4 이8 -- 름8
  부8 -- 르8 -- 시8 -- 던8 목4 -- 소4
  리2 \skip 4 지8 -- 금8
  도4 내4 귓8 -- 가8 -- 에4
  울8 -- 리8 -- 는4 데2
  아8 -- 무8 -- 도4 기8 -- 억8 \skip 4
  못8 -- 하8 -- 나4 보8 -- 다8 사8 -- 진8
  속4 우8 -- 리8 바8 -- 라8 -- 보8 -- 니8
  그8 -- 때8 -- 는4 \skip 2
  아8 -- 주8 평8 -- 범8 -- 했8 -- 구8 \skip 4
  나2 \skip 4 생8 -- 각8
  만4 해4 -- 도4 내4
  맘8 이8 -- 렇8 -- 게8 아8 -- 픈8 -- 데4
  아8 -- 무8 -- 도4 기8 -- 억8 \skip 4
  못8 -- 하8 -- 나4 보8 -- 다8 내8 -- 얘8
  % 후렴 1 (m22-37)
  기4 -- 만4 듣4 -- 고4
  가4 -- 세2 -- 요4
  한4 번4 -- 도8 용8 -- 기4
  내8 -- 지8 못4 -- 한8 \skip 8 평8 -- 생8
  을4 나4 기8 -- 억8 -- 할8 -- 게8
  요2 \skip 4 내4
  말4 듣4 -- 고4 가4
  세2 요4 저8 -- 기8
  요4 아8 -- 저8 -- 씨4 잠8 -- 시8
  만4 -- 요2 \skip 4
  사8 -- 진8 좀4 같8 -- 이8 \skip 4
  찍8 -- 어8 -- 주8 -- 세8 요4 언8 -- 젠8
  가4 당8 -- 신8 얼4 -- 굴4
  잊8 -- 어8 -- 버8 -- 릴8 까2
  내8 -- 는8 -- 요4 여8 -- 기8 \skip 4
  남8 -- 길8 -- 랍4 니4 -- 다4
  % 간주 (m38-45) — m45 끝에 "어느" 픽업
  \skip 1 \skip 1 \skip 1 \skip 1 \skip 1 \skip 1 \skip 1
  \skip 2. 어8 -- 느8
  % 2절 (m46-53)
  날4 갑8 -- 자8 -- 기4 생8 -- 각8
  이4 -- 나2 \skip 4
  손8 -- 잡8 -- 고4 거8 -- 닐8 -- 던4
  그8 -- 골8 -- 목8 -- 길8 하8 -- 나8 \skip 4
  둘4 셋4 걸8 -- 으8 -- 며4
  모8 -- 두8 좋8 -- 았8 -- 는8 -- 데8 \skip 4
  아8 -- 무8 -- 도4 기8 -- 억8 \skip 4
  못8 -- 하8 -- 나4 보8 -- 다8 내8 -- 얘8
  % 후렴 2 (m54-69) — 끝에 "내가" 픽업
  기4 -- 만4 듣4 -- 고4
  가4 -- 세2 -- 요4
  한4 번4 -- 도8 용8 -- 기4
  내8 -- 지8 못4 -- 한8 \skip 8 평8 -- 생8
  을4 나4 기8 -- 억8 -- 할8 -- 게8
  요2 \skip 4 내4
  말4 듣4 -- 고4 가4
  세2 요4 저8 -- 기8
  요4 아8 -- 저8 -- 씨4 잠8 -- 시8
  만4 -- 요2 \skip 4
  사8 -- 진8 좀4 같8 -- 이8 \skip 4
  찍8 -- 어8 -- 주8 -- 세8 요4 언8 -- 젠8
  가4 당8 -- 신8 얼4 -- 굴4
  잊8 -- 어8 -- 버8 -- 릴8 까2
  내8 -- 는8 -- 요4 여8 -- 기8 \skip 4
  남8 -- 길8 -- 랍4 니8 -- 다8 내8 -- 가8
  % 엔딩 (m70-72)
  요4 평4 -- 생4 기8 -- 억8
  할8 -- 게8 요2 \skip 4
  \skip 1
  % 아웃트로 (m73-76)
  \skip 1 \skip 1 \skip 1 \skip 1
}

%%% ---------- 악보 ----------

\score {
  <<
    \new ChordNames { \allChords }
    \new Staff { \clef "treble_8" \music }
    \new Lyrics { \allLyrics }
    \new TabStaff {
      \removeWithTag #'marks \music
    }
  >>
  \layout {
    \context {
      \Score
      \override RehearsalMark.self-alignment-X = #LEFT
    }
    \context {
      \Staff
      \override StringNumber.stencil = ##f
    }
  }
}
