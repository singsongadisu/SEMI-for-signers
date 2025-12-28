/**
 * SEMI AI Gesture Engine
 * Powered by MediaPipe Hand Landmarker
 */

class AIGestureEngine {
    constructor() {
        this.handLandmarker = null;
        this.wasmUrl = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm";
        this.modelAssetPath = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
        this.runningMode = "VIDEO";
        this.isInitialized = false;
        this.lastVideoTime = -1;
        this.ghostImage = null;

        // Universal Amharic Semantic Bridge (STRICT & COMPREHENSIVE)
        // Grouped by root families to ensure no overlaps (e.g. Ha vs Le vs Me)
        this.AMHARIC_MAP = {
            // HA Family (ሀ, ሐ) - Flat Hand
            'ሀ': ['LETTER B', 'NUMBER 4'], 'ሁ': ['LETTER B', 'NUMBER 4'], 'ሂ': ['LETTER B', 'NUMBER 4'], 'ሃ': ['LETTER B', 'NUMBER 4'], 'ሄ': ['LETTER B', 'NUMBER 4'], 'ህ': ['LETTER B', 'NUMBER 4'], 'ሆ': ['LETTER B', 'NUMBER 4'],
            'ሐ': ['LETTER B', 'NUMBER 4'], 'ሑ': ['LETTER B', 'NUMBER 4'], 'ሒ': ['LETTER B', 'NUMBER 4'], 'ሓ': ['LETTER B', 'NUMBER 4'], 'ሔ': ['LETTER B', 'NUMBER 4'], 'ሕ': ['LETTER B', 'NUMBER 4'], 'ሖ': ['LETTER B', 'NUMBER 4'],

            // LE Family (ለ) - Pinch
            'ለ': ['LETTER F'], 'ሉ': ['LETTER F'], 'ሊ': ['LETTER F'], 'ላ': ['LETTER F'], 'ሌ': ['LETTER F'], 'ል': ['LETTER F'], 'ሎ': ['LETTER F'],

            // ME Family (መ) - M-Fist
            'መ': ['LETTER M'], 'ሙ': ['LETTER M'], 'ሚ': ['LETTER M'], 'ማ': ['LETTER M'], 'ሜ': ['LETTER M'], 'ም': ['LETTER M'], 'ሞ': ['LETTER M'],

            // RE Family (ረ) - Crossed
            'ረ': ['LETTER R'], 'ሩ': ['LETTER R'], 'ሪ': ['LETTER R'], 'ራ': ['LETTER R'], 'ሬ': ['LETTER R'], 'ር': ['LETTER R'], 'ሮ': ['LETTER R'],

            // SE/SHE/SSA Family (ሰ, ሸ, ሠ) - S-Fist
            'ሰ': ['LETTER S'], 'ሱ': ['LETTER S'], 'ሲ': ['LETTER S'], 'ሳ': ['LETTER S'], 'ሴ': ['LETTER S'], 'ስ': ['LETTER S'], 'ሶ': ['LETTER S'],
            'ሸ': ['LETTER S'], 'ሹ': ['LETTER S'], 'ሺ': ['LETTER S'], 'ሻ': ['LETTER S'], 'ሼ': ['LETTER S'], 'ሽ': ['LETTER S'], 'ሾ': ['LETTER S'],
            'ሠ': ['LETTER S'], 'ሡ': ['LETTER S'], 'ሢ': ['LETTER S'], 'ሣ': ['LETTER S'], 'ሤ': ['LETTER S'], 'ሥ': ['LETTER S'], 'ሦ': ['LETTER S'],

            // KE Family (ቀ) - Down Pinch (Q)
            'ቀ': ['LETTER Q'], 'ቁ': ['LETTER Q'], 'ቂ': ['LETTER Q'], 'ቃ': ['LETTER Q'], 'ቄ': ['LETTER Q'], 'ቅ': ['LETTER Q'], 'ቆ': ['LETTER Q'],

            // BE Family (በ) - Flat B
            'በ': ['LETTER B'], 'ቡ': ['LETTER B'], 'ቢ': ['LETTER B'], 'ባ': ['LETTER B'], 'ቤ': ['LETTER B'], 'ብ': ['LETTER B'], 'ቦ': ['LETTER B'],

            // TE/CHE Family (ተ, ቸ) - T-Fist
            'ተ': ['LETTER T'], 'ቱ': ['LETTER T'], 'ቲ': ['LETTER T'], 'ታ': ['LETTER T'], 'ቴ': ['LETTER T'], 'ት': ['LETTER T'], 'ቶ': ['LETTER T'],
            'ቸ': ['LETTER T'], 'ቹ': ['LETTER T'], 'ቺ': ['LETTER T'], 'ቻ': ['LETTER T'], 'ቼ': ['LETTER T'], 'ች': ['LETTER T'], 'ቾ': ['LETTER T'],

            // NE/NYE Family (ነ, ኘ) - N-Fist
            'ነ': ['LETTER N'], 'ኑ': ['LETTER N'], 'ኒ': ['LETTER N'], 'ና': ['LETTER N'], 'ኔ': ['LETTER N'], 'ን': ['LETTER N'], 'ኖ': ['LETTER N'],
            'ኘ': ['LETTER N'], 'ኙ': ['LETTER N'], 'ኚ': ['LETTER N'], 'ኛ': ['LETTER N'], 'ኜ': ['LETTER N'], 'ኝ': ['LETTER N'], 'ኞ': ['LETTER N'],

            // A/AYNE Family (አ, ዐ) - A or O
            'አ': ['LETTER A'], 'ኡ': ['LETTER A'], 'ኢ': ['LETTER A'], 'ኣ': ['LETTER A'], 'ኤ': ['LETTER A'], 'እ': ['LETTER A'], 'ኦ': ['LETTER A'],
            'ዐ': ['LETTER O'], 'ዑ': ['LETTER O'], 'ዒ': ['LETTER O'], 'ዓ': ['LETTER O'], 'ዔ': ['LETTER O'], 'ዕ': ['LETTER O'], 'ዖ': ['LETTER O'],

            // KE Family (ከ) - C shape
            'ከ': ['LETTER C'], 'ኩ': ['LETTER C'], 'ኪ': ['LETTER C'], 'ካ': ['LETTER C'], 'ኬ': ['LETTER C'], 'ክ': ['LETTER C'], 'ኮ': ['LETTER C'],

            // WE Family (ወ) - W shape
            'ወ': ['LETTER W'], 'ዉ': ['LETTER W'], 'ዊ': ['LETTER W'], 'ዋ': ['LETTER W'], 'ዌ': ['LETTER W'], 'ው': ['LETTER W'], 'ዎ': ['LETTER W'],

            // ZE/ZHE Family (ዘ, ዠ) - Z/S shape
            'ዘ': ['LETTER S'], 'ዙ': ['LETTER S'], 'ዚ': ['LETTER S'], 'ዛ': ['LETTER S'], 'ዜ': ['LETTER S'], 'ዝ': ['LETTER S'], 'ዞ': ['LETTER S'],
            'ዠ': ['LETTER S'], 'ዡ': ['LETTER S'], 'ዢ': ['LETTER S'], 'ዣ': ['LETTER S'], 'ዤ': ['LETTER S'], 'ዥ': ['LETTER S'], 'ዦ': ['LETTER S'],

            // YE Family (የ) - Y shape
            'የ': ['LETTER Y'], 'ዩ': ['LETTER Y'], 'ዪ': ['LETTER Y'], 'ያ': ['LETTER Y'], 'ዬ': ['LETTER Y'], 'ይ': ['LETTER Y'], 'ዮ': ['LETTER Y'],

            // DE/JE Family (ደ, ጀ) - D shape
            'ደ': ['LETTER D'], 'ዱ': ['LETTER D'], 'ዲ': ['LETTER D'], 'ዳ': ['LETTER D'], 'ዴ': ['LETTER D'], 'ድ': ['LETTER D'], 'ዶ': ['LETTER D'],
            'ጀ': ['LETTER D'], 'ጁ': ['LETTER D'], 'ጂ': ['LETTER D'], 'ጃ': ['LETTER D'], 'ጄ': ['LETTER D'], 'ጅ': ['LETTER D'], 'ጆ': ['LETTER D'],

            // GE/T'E/CH'E Family (ገ, ጠ, ጨ) - G shape
            'ገ': ['LETTER G'], 'ጉ': ['LETTER G'], 'ጊ': ['LETTER G'], 'ጋ': ['LETTER G'], 'ጌ': ['LETTER G'], 'ግ': ['LETTER G'], 'ጎ': ['LETTER G'],
            'ጠ': ['LETTER G'], 'ጡ': ['LETTER G'], 'ጢ': ['LETTER G'], 'ጣ': ['LETTER G'], 'ጤ': ['LETTER G'], 'ጥ': ['LETTER G'], 'ጦ': ['LETTER G'],
            'ጨ': ['LETTER G'], 'ጩ': ['LETTER G'], 'ጪ': ['LETTER G'], 'ጫ': ['LETTER G'], 'ጬ': ['LETTER G'], 'ጭ': ['LETTER G'], 'ጮ': ['LETTER G'],

            // FE Family (ፈ) - F shape
            'ፈ': ['LETTER F'], 'ፉ': ['LETTER F'], 'ፊ': ['LETTER F'], 'ፋ': ['LETTER F'], 'ፌ': ['LETTER F'], 'ፍ': ['LETTER F'], 'ፎ': ['LETTER F'],

            // PE/P'E Family (ጰ, ፐ) - P shape
            'ጰ': ['LETTER P'], 'ጱ': ['LETTER P'], 'ጲ': ['LETTER P'], 'ጳ': ['LETTER P'], 'ጴ': ['LETTER P'], 'ጵ': ['LETTER P'], 'ጶ': ['LETTER P'],
            'ፐ': ['LETTER P'], 'ፑ': ['LETTER P'], 'ፒ': ['LETTER P'], 'ፓ': ['LETTER P'], 'ፔ': ['LETTER P'], 'ፕ': ['LETTER P'], 'ፖ': ['LETTER P']
        };
    }

    async initialize() {
        try {
            const vision = await FilesetResolver.forVisionTasks(
                "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
            );
            this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: this.modelAssetPath,
                    delegate: "CPU" // Switched to CPU for max reliability in school environments
                },
                runningMode: this.runningMode,
                numHands: 1,
                minHandDetectionConfidence: 0.1, // Max sensitivity for small signs like 'Le'
                minHandPresenceConfidence: 0.1,
                minTrackingConfidence: 0.1
            });
            this.isInitialized = true;
            console.log("SEMI AI: Hand Landmarker Initialized");
            return true;
        } catch (error) {
            console.error("SEMI AI: Initialization Failed", error);
            return false;
        }
    }

    predict(video) {
        if (!this.isInitialized || !this.handLandmarker) return null;

        // Ensure video is ready to prevent RET_CHECK failure
        if (video.readyState < 2 || video.videoWidth === 0) return null;

        let startTimeMs = performance.now();
        if (this.lastVideoTime !== video.currentTime) {
            this.lastVideoTime = video.currentTime;
            return this.handLandmarker.detectForVideo(video, startTimeMs);
        }
        return null;
    }

    /**
     * Logic to detect specific signs based on landmarks
     * landmarks is an array of 21 points {x, y, z}
     */
    detectGesture(results, targetSign = "", templateLandmarks = null) {
        if (!results || !results.landmarks || results.landmarks.length === 0)
            return { gesture: "NONE", hints: [] };

        const hand = results.landmarks[0];
        const handedness = results.handedness ? results.handedness[0][0].categoryName : "Right";
        const target = targetSign.toUpperCase();

        // 1. If we have a visual template (for Amharic), use Distance Comparison
        if (templateLandmarks) {
            const similarity = this.comparePoses(hand, templateLandmarks);

            // Threshold for a match (lower is closer)
            // 0.15 is generally a good "strict" match, 0.20 is "medium"
            const matched = similarity < 0.19;

            if (matched) {
                // If the target is Amharic, we celebrate the visual match directly
                return { gesture: "MATCHED!", hints: [], score: similarity, isTemplateMatch: true };
            } else if (similarity < 0.35) {
                // Determine the most problematic area for coaching
                const hint = this.getSimilarityHint(hand, templateLandmarks);
                return { gesture: "ALIGNING...", hints: [hint], score: similarity };
            }
        }

        // 2. Fallback to hard-coded Heuristics for ASL
        const resultsMap = {
            "LETTER A": this.isLetterA(hand),
            "LETTER B": this.isLetterB(hand),
            "LETTER C": this.isLetterC(hand),
            "LETTER D": this.isLetterD(hand),
            "LETTER E": this.isLetterE(hand),
            "LETTER F": this.isLetterF(hand),
            "LETTER G": this.isLetterG(hand),
            "LETTER H": this.isLetterH(hand),
            "LETTER I": this.isLetterI(hand),
            "LETTER J": this.isLetterJ(hand),
            "LETTER K": this.isLetterK(hand),
            "LETTER L": this.isLetterL(hand),
            "LETTER M": this.isLetterM(hand),
            "LETTER N": this.isLetterN(hand),
            "LETTER O": this.isLetterO(hand),
            "LETTER P": this.isLetterP(hand),
            "LETTER Q": this.isLetterQ(hand),
            "LETTER R": this.isLetterR(hand, handedness),
            "LETTER S": this.isLetterS(hand),
            "LETTER T": this.isLetterT(hand),
            "LETTER U": this.isLetterU(hand),
            "LETTER V": this.isLetterV(hand, handedness),
            "LETTER W": this.isLetterW(hand),
            "LETTER X": this.isLetterX(hand),
            "LETTER Y": this.isLetterY(hand),
            "LETTER Z": this.isLetterZ(hand),
            "NUMBER 1": this.isNumber1(hand),
            "NUMBER 2": this.isNumber2(hand),
            "NUMBER 3": this.isNumber3(hand),
            "NUMBER 4": this.isNumber4(hand),
            "NUMBER 5": this.isNumber5(hand),
            "NUMBER 6": this.isNumber6(hand),
            "NUMBER 7": this.isNumber7(hand),
            "NUMBER 8": this.isNumber8(hand),
            "NUMBER 9": this.isNumber9(hand),
            "NUMBER 10": this.isNumber10(hand),
            "NUMBER 20": this.isNumber20(hand),
            "NUMBER 30": this.isNumber30(hand),
            "NUMBER 40": this.isNumber40(hand),
            "NUMBER 50": this.isNumber50(hand),
            "NUMBER 60": this.isNumber60(hand),
            "NUMBER 70": this.isNumber70(hand),
            "NUMBER 80": this.isNumber80(hand),
            "NUMBER 90": this.isNumber90(hand),
            "NUMBER 100": { match: this.isLetterC(hand).match, hints: ["Form a 'C' shape for 100"] },
            "HELLO": { match: this.isHello(hand), hints: [] },
            "YES": { match: this.isYes(hand), hints: [] },
            "NO": { match: this.isNo(hand), hints: [] }
        };

        // PRIORITY 1: Targeted Amharic Search (Zero Tolerance)
        const amharicChars = (targetSign || "").match(/[\u1200-\u137F]/g);
        if (amharicChars && amharicChars.length > 0) {
            const currentChar = amharicChars[0];
            const allowedShapes = this.AMHARIC_MAP[currentChar];

            if (allowedShapes) {
                const shapesToCheck = Array.isArray(allowedShapes) ? allowedShapes : [allowedShapes];
                for (const shape of shapesToCheck) {
                    if (resultsMap[shape] && resultsMap[shape].match) {
                        return { gesture: "MATCHED!", hints: [] };
                    }
                }
            }
            // Smart Coaching: Show hints specifically for this character's required shape
            const firstShape = Array.isArray(allowedShapes) ? allowedShapes[0] : allowedShapes;
            const hints = (resultsMap[firstShape] && resultsMap[firstShape].hints) || [];
            return { gesture: "SCANNING FOR POSE...", hints: hints };
        }

        // PRIORITY 2: Check Visual Template (Specific Lesson Fingerprint)
        if (templateLandmarks) {
            const similarity = this.comparePoses(hand, templateLandmarks);
            // Strict threshold for Amharic
            if (similarity < 0.16) {
                return { gesture: "MATCHED!", hints: [], score: similarity };
            }
        }

        // PRIORITY 3: Standard ASL labeling (Only for ASL Lessons)
        let detectedGesture = "TRACKING...";
        for (const [name, res] of Object.entries(resultsMap)) {
            if (res.match) {
                detectedGesture = name;
                break;
            }
        }

        // Extract hints for the target sign (Context-Aware)
        const coachingHints = [];
        for (const [name, res] of Object.entries(resultsMap)) {
            const cleanName = name.replace('LETTER ', '').replace('NUMBER ', '');
            const regex = new RegExp(`\\b${cleanName}\\b`, 'i');

            if (regex.test(target)) {
                if (detectedGesture !== name && res.hints && res.hints.length > 0) {
                    coachingHints.push(...res.hints);
                }
            }
        }

        // Frame Smoothing Logic: Require 2 consistent frames for a match
        if (detectedGesture === "MATCHED!") {
            this.matchCounter = (this.matchCounter || 0) + 1;
            if (this.matchCounter < 2) detectedGesture = "SCANNING...";
        } else {
            this.matchCounter = 0;
        }

        return { gesture: detectedGesture, hints: coachingHints };
    }

    /**
     * Fully resets the AI state to prevent memory leaks or logic fatigue
     */
    clearState() {
        this.matchCounter = 0;
        this.lastVideoTime = -1;
        console.log("SEMI AI: State Cleared for New Character");
    }

    /**
     * Specialized logic to detect if the hand is present but no gesture is matched
     */
    getFallbackGesture(results) {
        if (!results || !results.landmarks || results.landmarks.length === 0) {
            return "NO HAND DETECTED";
        }
        return "ADJUSTING...";
    }

    /**
     * Captures hand landmarks from a static image to use as a template.
     * Uses a temporary canvas and multiple retries to handle complex backgrounds.
     */
    async captureTemplate(image, retries = 5) {
        if (!this.handLandmarker) return null;

        // Wait for image content
        if (!image.complete || image.naturalWidth === 0) {
            await new Promise(r => {
                image.onload = r;
                setTimeout(r, 1000);
            });
        }

        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = 1280;
                tempCanvas.height = 720;
                const tempCtx = tempCanvas.getContext('2d');

                const scale = Math.min(tempCanvas.width / image.naturalWidth, tempCanvas.height / image.naturalHeight);
                const x = (tempCanvas.width - image.naturalWidth * scale) / 2;
                const y = (tempCanvas.height - image.naturalHeight * scale) / 2;
                tempCtx.drawImage(image, x, y, image.naturalWidth * scale, image.naturalHeight * scale);

                const results = this.handLandmarker.detectForVideo(tempCanvas, performance.now());

                // Cleanup canvas immediately to save memory
                tempCanvas.width = 0;
                tempCanvas.height = 0;

                if (results && results.landmarks && results.landmarks.length > 0) {
                    console.log(`SEMI AI: Fingerprint captured (Attempt ${attempt + 1}) ✅`);
                    return results.landmarks[0];
                }

                await new Promise(r => setTimeout(r, 200));
            } catch (error) {
                console.error("SEMI AI: Scan Error", error);
            }
        }

        console.warn("SEMI AI: Image scan failed. Falling back to Semantic Bridge.");
        return null;
    }

    /**
     * Compares two sets of 21 landmarks using normalized Euclidean distance
     */
    comparePoses(current, template) {
        // 1. Normalize both hands
        const normCurrent = this.normalizeHand(current);
        const normTemplate = this.normalizeHand(template);

        // 2. Calculate Sum of Squared Errors
        let totalDist = 0;
        for (let i = 0; i < 21; i++) {
            const dx = normCurrent[i].x - normTemplate[i].x;
            const dy = normCurrent[i].y - normTemplate[i].y;
            const dz = normCurrent[i].z - normTemplate[i].z;
            totalDist += Math.sqrt(dx * dx + dy * dy + dz * dz);
        }

        // Return average distance per landmark
        return totalDist / 21;
    }

    /**
     * Normalizes hand landmarks:
     * - Shifts wrist (0) to (0,0,0)
     * - Scales so the palm size (Wrist to Middle Finger MCP) is 1.0
     */
    normalizeHand(landmarks) {
        const wrist = landmarks[0];
        const mcp = landmarks[9]; // Middle finger MCP

        // Calculate palm size for scaling
        const scale = Math.sqrt(
            Math.pow(mcp.x - wrist.x, 2) +
            Math.pow(mcp.y - wrist.y, 2) +
            Math.pow(mcp.z - wrist.z, 2)
        ) || 1.0;

        return landmarks.map(p => ({
            x: (p.x - wrist.x) / scale,
            y: (p.y - wrist.y) / scale,
            z: (p.z - wrist.z) / scale,
            raw: p // keep raw for coaching
        }));
    }

    /**
     * Analyzes coordinate differences to provide actionable coaching advice
     */
    getSimilarityHint(current, template) {
        const normCurrent = this.normalizeHand(current);
        const normTemplate = this.normalizeHand(template);

        // Check fingertips (8, 12, 16, 20)
        let mostOff = -1;
        let maxError = 0;
        [8, 12, 16, 20, 4].forEach(idx => {
            const err = Math.abs(normCurrent[idx].y - normTemplate[idx].y);
            if (err > maxError) {
                maxError = err;
                mostOff = idx;
            }
        });

        if (mostOff === 4) return "Adjust your thumb position";
        if (mostOff === 8) return "Check your index finger alignment";
        if (mostOff === 12) return "Adjust your middle finger";
        if (maxError > 0.4) return "Try to mimic the ghost image more closely";

        return "You're close! Keep adjusting slightly";
    }

    // --- HEURISTICS ---

    // HELLO: All fingers extended AND spread apart
    isHello(hand) {
        const fingerTips = [8, 12, 16, 20];
        const fingerBases = [5, 9, 13, 17];
        const allUp = fingerTips.every((tip, i) => hand[tip].y < hand[fingerBases[i]].y);

        // Spread check: distance between index and pinky tip should be large
        const spread = Math.abs(hand[8].x - hand[20].x);
        return allUp && spread > 0.3;
    }

    // YES: Closed fist
    isYes(hand) {
        const fingerTips = [8, 12, 16, 20];
        const fingerPIP = [6, 10, 14, 18];
        return fingerTips.every((tip, i) => hand[tip].y > hand[fingerPIP[i]].y);
    }

    // NO: Index and middle fingers extended, thumb touching them
    isNo(hand) {
        const isIndexExt = hand[8].y < hand[6].y;
        const isMiddleExt = hand[12].y < hand[10].y;
        const isRingCurled = hand[16].y > hand[14].y;
        const isPinkyCurled = hand[20].y > hand[18].y;
        return isIndexExt && isMiddleExt && isRingCurled && isPinkyCurled;
    }

    // --- NUMBERS ---
    isNumber1(hand) {
        const indexUp = hand[8].y < hand[6].y;
        const middleDown = hand[12].y > hand[10].y;
        const ringDown = hand[16].y > hand[14].y;
        const hints = [];
        if (!indexUp) hints.push("Extend your index finger upwards");
        if (middleDown === false) hints.push("Curle your other fingers");
        return { match: indexUp && middleDown && ringDown, hints };
    }

    isNumber2(hand) {
        const indexUp = hand[8].y < hand[6].y;
        const middleUp = hand[12].y < hand[10].y;
        const ringDown = hand[16].y > hand[14].y;
        const hints = [];
        if (!indexUp || !middleUp) hints.push("Extend index and middle fingers (V shape)");
        if (ringDown === false) hints.push("Keep ring and pinky fingers down");
        return { match: indexUp && middleUp && ringDown, hints };
    }

    isNumber3(hand) {
        const thumbOut = Math.abs(hand[4].x - hand[13].x) > 0.1;
        const indexUp = hand[8].y < hand[6].y;
        const middleUp = hand[12].y < hand[10].y;
        const ringDown = hand[16].y > hand[14].y;
        const hints = [];
        if (!thumbOut) hints.push("Extend your thumb outwards");
        if (!indexUp || !middleUp) hints.push("Extend index and middle fingers");
        return { match: thumbOut && indexUp && middleUp && ringDown, hints };
    }

    isNumber4(hand) {
        const allUp = [8, 12, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const thumbTucked = hand[4].x < hand[5].x || Math.abs(hand[4].x - hand[5].x) < 0.05;
        const hints = [];
        if (!allUp) hints.push("Straighten your four fingers");
        if (!thumbTucked) hints.push("Tuck your thumb into your palm");
        return { match: allUp && thumbTucked, hints };
    }

    isNumber5(hand) {
        const allUp = [8, 12, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const thumbOut = Math.abs(hand[4].x - hand[2].x) > 0.1;
        const spread = Math.abs(hand[8].x - hand[20].x) > 0.2;
        const hints = [];
        if (!allUp) hints.push("Extend all five fingers");
        if (!thumbOut) hints.push("Spread your thumb away from palm");
        if (!spread) hints.push("Spread your fingers apart");
        return { match: allUp && thumbOut && spread, hints };
    }

    isNumber6(hand) {
        const thumbPinkyTouch = Math.hypot(hand[4].x - hand[20].x, hand[4].y - hand[20].y) < 0.08;
        const othersUp = [8, 12, 16].every(tip => hand[tip].y < hand[tip - 2].y);
        const hints = [];
        if (!thumbPinkyTouch) hints.push("Touch your thumb to your pinky finger");
        if (!othersUp) hints.push("Keep your index, middle, and ring fingers up");
        return { match: thumbPinkyTouch && othersUp, hints };
    }

    isNumber7(hand) {
        const thumbRingTouch = Math.hypot(hand[4].x - hand[16].x, hand[4].y - hand[16].y) < 0.08;
        const othersUp = [8, 12, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const hints = [];
        if (!thumbRingTouch) hints.push("Touch your thumb to your ring finger");
        if (!othersUp) hints.push("Keep other fingers extended");
        return { match: thumbRingTouch && othersUp, hints };
    }

    isNumber8(hand) {
        const thumbMiddleTouch = Math.hypot(hand[4].x - hand[12].x, hand[4].y - hand[12].y) < 0.08;
        const othersUp = [8, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const hints = [];
        if (!thumbMiddleTouch) hints.push("Touch your thumb to your middle finger");
        if (!othersUp) hints.push("Keep other fingers extended");
        return { match: thumbMiddleTouch && othersUp, hints };
    }

    isNumber9(hand) {
        const thumbIndexTouch = Math.hypot(hand[4].x - hand[8].x, hand[4].y - hand[8].y) < 0.08;
        const othersUp = [12, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const hints = [];
        if (!thumbIndexTouch) hints.push("Touch your thumb to your index finger");
        if (!othersUp) hints.push("Keep other fingers extended");
        return { match: thumbIndexTouch && othersUp, hints };
    }

    isNumber10(hand) {
        const thumbUp = hand[4].y < hand[3].y && hand[4].y < hand[5].y;
        const fist = [8, 12, 16, 20].every(tip => hand[tip].y > hand[tip - 1].y);
        const hints = [];
        if (!thumbUp) hints.push("Point your thumb straight up");
        if (!fist) hints.push("Close your other fingers into a fist");
        return { match: thumbUp && fist, hints };
    }

    isNumber20(hand) {
        const indexThumbPinch = Math.hypot(hand[4].x - hand[8].x, hand[4].y - hand[8].y) < 0.08;
        const othersClosed = [12, 16, 20].every(tip => hand[tip].y > hand[tip - 1].y);
        const hints = [];
        if (!indexThumbPinch) hints.push("Pinch your index and thumb together");
        if (!othersClosed) hints.push("Keep your other fingers curled");
        return { match: indexThumbPinch && othersClosed, hints };
    }

    isNumber30(hand) {
        // Looks like 3 but with thumb/fingers moving. Static: 3 pose with fingers slightly curved.
        const res = this.isNumber3(hand);
        res.hints.push("Curle fingers slightly for the '0' transition");
        return res;
    }

    isNumber40(hand) {
        const res = this.isNumber4(hand);
        res.hints.push("Curle fingers slightly for the '0' transition");
        return res;
    }

    isNumber50(hand) {
        const res = this.isNumber5(hand);
        res.hints.push("Curle fingers slightly for the '0' transition");
        return res;
    }

    isNumber60(hand) { return this.isNumber6(hand); }
    isNumber70(hand) { return this.isNumber7(hand); }
    isNumber80(hand) { return this.isNumber8(hand); }
    isNumber90(hand) { return this.isNumber9(hand); }

    // --- LETTERS ---
    isLetterL(hand) {
        const indexUp = hand[8].y < hand[6].y;
        const thumbOut = Math.abs(hand[4].x - hand[2].x) > 0.1;
        const middleCurled = hand[12].y > hand[10].y;
        const hints = [];
        if (!indexUp) hints.push("Point your index finger up");
        if (!thumbOut) hints.push("Stretch your thumb out for an 'L' shape");
        return { match: indexUp && thumbOut && middleCurled, hints };
    }

    isLetterV(hand, handedness = "Right") {
        const indexUp = hand[8].y < hand[6].y;
        const middleUp = hand[12].y < hand[10].y;
        const ringCurled = hand[16].y > hand[14].y;

        // Spread check: distance between tips
        const dist = Math.hypot(hand[8].x - hand[12].x, hand[8].y - hand[12].y);

        const hints = [];
        if (!indexUp || !middleUp) hints.push("Show the peace sign (V shape)");
        if (dist < 0.08) hints.push("Spread your fingers wider for 'V'");

        const match = indexUp && middleUp && ringCurled && dist > 0.08;
        return { match, hints };
    }

    // LETTER B: Open palm, fingers together, thumb tucked
    isLetterB(hand) {
        // Tightened: must be very straight and together
        const fingersUp = [8, 12, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const together = Math.abs(hand[8].x - hand[12].x) < 0.05;
        const thumbIn = hand[4].x < hand[5].x || Math.abs(hand[4].x - hand[5].x) < 0.04;
        const hints = [];
        if (!fingersUp) hints.push("Straighten all your fingers");
        if (!thumbIn) hints.push("Fold your thumb tighter across your palm");
        return { match: fingersUp && thumbIn && together, hints };
    }

    isLetterD(hand) {
        const indexUp = hand[8].y < hand[6].y;
        const circle = [12, 16, 20].every(tip => Math.hypot(hand[tip].x - hand[4].x, hand[tip].y - hand[4].y) < 0.1);
        const hints = [];
        if (!indexUp) hints.push("Point your index finger straight up");
        if (!circle) hints.push("Touch your thumb to the other three fingers");
        return { match: indexUp && circle, hints };
    }

    isLetterE(hand) {
        const fingerTips = [8, 12, 16, 20];
        const allCurled = fingerTips.every(tip => hand[tip].y > hand[tip - 1].y);
        const thumbTucked = hand[4].y > hand[14].y;
        const hints = [];
        if (!allCurled) hints.push("Curl all fingers tightly");
        if (!thumbTucked) hints.push("Tuck your thumb under your fingers");
        return { match: allCurled && thumbTucked, hints };
    }

    // LETTER F: Index and Thumb touch, others up
    isLetterF(hand) {
        // Balanced threshold (0.18) - Strict but achievable for students
        const okCircle = Math.hypot(hand[8].x - hand[4].x, hand[8].y - hand[4].y) < 0.18;
        const otherFingersUp = [12, 16, 20].every(tip => hand[tip].y < hand[tip - 2].y);
        const hints = [];
        if (!okCircle) hints.push("Touch your index finger and thumb together");
        if (!otherFingersUp) hints.push("Spread your other three fingers up");
        return { match: okCircle && otherFingersUp, hints };
    }

    isLetterG(hand) {
        const indexOut = Math.abs(hand[8].x - hand[6].x) > 0.1 && hand[8].y < hand[5].y + 0.1;
        const thumbOut = Math.abs(hand[4].x - hand[2].x) > 0.1;
        const othersClosed = [12, 16, 20].every(tip => hand[tip].x < hand[tip - 2].x + 0.05);
        const hints = [];
        if (!indexOut) hints.push("Point your index finger sideways");
        if (!thumbOut) hints.push("Point your thumb parallel to your index");
        return { match: indexOut && thumbOut && othersClosed, hints };
    }

    isLetterH(hand) {
        const indexOut = Math.abs(hand[8].x - hand[6].x) > 0.1;
        const middleOut = Math.abs(hand[12].x - hand[10].x) > 0.1;
        const together = Math.hypot(hand[8].x - hand[12].x, hand[8].y - hand[12].y) < 0.08;
        const hints = [];
        if (!indexOut || !middleOut) hints.push("Extend index and middle fingers sideways");
        if (!together) hints.push("Keep index and middle fingers together");
        return { match: indexOut && middleOut && together, hints };
    }

    isLetterI(hand) {
        const pinkyUp = hand[20].y < hand[18].y;
        const othersClosed = [8, 12, 16].every(tip => hand[tip].y > hand[tip - 2].y);
        const hints = [];
        if (!pinkyUp) hints.push("Extend your pinky finger straight up");
        if (!othersClosed) hints.push("Curl your other fingers tightly");
        return { match: pinkyUp && othersClosed, hints };
    }

    isLetterJ(hand) {
        // Static pose same as I for now
        return this.isLetterI(hand);
    }

    isLetterK(hand) {
        const indexUp = hand[8].y < hand[6].y;
        const middleUp = hand[12].y < hand[10].y;
        const thumbBetween = hand[4].y < hand[10].y && hand[4].y > hand[12].y;
        const hints = [];
        if (!indexUp) hints.push("Extend your index finger up");
        if (!middleUp) hints.push("Extend your middle finger slightly forward");
        if (!thumbBetween) hints.push("Place your thumb against your middle finger");
        return { match: indexUp && middleUp && thumbBetween, hints };
    }

    isLetterM(hand) {
        const fingerTips = [8, 12, 16];
        const allCurled = fingerTips.every(tip => hand[tip].y > hand[tip - 1].y);
        const thumbUnder = hand[4].x < hand[17].x && hand[4].y > hand[16].y;
        const hints = [];
        if (!allCurled) hints.push("Curl your fingers down");
        if (!thumbUnder) hints.push("Tuck your thumb under three fingers");
        return { match: allCurled && thumbUnder, hints };
    }

    isLetterN(hand) {
        const indexMiddleCurled = [8, 12].every(tip => hand[tip].y > hand[tip - 1].y);
        const thumbUnder = hand[4].x < hand[13].x && hand[4].y > hand[12].y;
        const hints = [];
        if (!indexMiddleCurled) hints.push("Curl your fingers down");
        if (!thumbUnder) hints.push("Tuck your thumb under two fingers");
        return { match: indexMiddleCurled && thumbUnder, hints };
    }

    isLetterO(hand) {
        const fingerTips = [8, 12, 16, 20];
        const allTouchThumb = fingerTips.every(tip => Math.hypot(hand[tip].x - hand[4].x, hand[tip].y - hand[4].y) < 0.1);
        const hints = [];
        if (!allTouchThumb) hints.push("Form a perfect 'O' shape with all fingers");
        return { match: allTouchThumb, hints };
    }

    isLetterP(hand) {
        // Like K but pointing down
        const res = this.isLetterK(hand);
        const pointingDown = hand[8].y > hand[5].y;
        if (!pointingDown) res.hints.push("Point your hand downwards");
        res.match = res.match && pointingDown;
        return res;
    }

    isLetterQ(hand) {
        // Like G but pointing down
        const res = this.isLetterG(hand);
        const pointingDown = hand[8].y > hand[5].y;
        if (!pointingDown) res.hints.push("Point your fingers downwards");
        res.match = res.match && pointingDown;
        return res;
    }

    isLetterR(hand, handedness = "Right") {
        const indexMiddleUp = hand[8].y < hand[6].y && hand[12].y < hand[10].y;

        // Crossing check: Tips are very close AND crossed
        // On right hand palm forward: middle(12) is left of index(8)
        // On left hand palm forward: middle(12) is right of index(8)
        // MediaPipe reports categoryName as "Right" or "Left" based on the actual hand.
        let crossed = false;
        if (handedness === "Right") {
            crossed = hand[12].x < hand[8].x;
        } else {
            crossed = hand[12].x > hand[8].x;
        }

        const dist = Math.hypot(hand[8].x - hand[12].x, hand[8].y - hand[12].y);
        const match = indexMiddleUp && crossed && dist < 0.06;

        const hints = [];
        if (!indexMiddleUp) hints.push("Extend index and middle fingers up");
        if (!crossed || dist >= 0.06) hints.push("Cross your middle finger tight over your index");

        return { match, hints };
    }

    isLetterS(hand) {
        const fist = [8, 12, 16, 20].every(tip => hand[tip].y > hand[tip - 2].y);
        const thumbOnTop = hand[4].y < hand[10].y && hand[4].x < hand[13].x;
        const hints = [];
        if (!fist) hints.push("Close your hand into a tight fist");
        if (!thumbOnTop) hints.push("Rest your thumb on top of your fingers");
        return { match: fist && thumbOnTop, hints };
    }

    isLetterT(hand) {
        const fingersCurled = [8, 12, 16, 20].every(tip => hand[tip].y > hand[tip - 2].y);
        const thumbUnderIndex = hand[4].y < hand[7].y && hand[4].x < hand[9].x;
        const hints = [];
        if (!fingersCurled) hints.push("Curl all your fingers");
        if (!thumbUnderIndex) hints.push("Tuck your thumb under your index finger");
        return { match: fingersCurled && thumbUnderIndex, hints };
    }

    isLetterU(hand) {
        const indexMiddleUp = hand[8].y < hand[6].y && hand[12].y < hand[10].y;
        const together = Math.abs(hand[8].x - hand[12].x) < 0.05;
        const hints = [];
        if (!indexMiddleUp) hints.push("Extend index and middle fingers up");
        if (!together) hints.push("Keep your index and middle fingers together");
        return { match: indexMiddleUp && together, hints };
    }

    isLetterW(hand) {
        const threeUp = [8, 12, 16].every(tip => hand[tip].y < hand[tip - 2].y);
        const spread = Math.abs(hand[8].x - hand[16].x) > 0.1;
        const pinkyDown = hand[20].y > hand[18].y;
        const hints = [];
        if (!threeUp) hints.push("Extend index, middle, and ring fingers");
        if (!spread) hints.push("Spread your fingers into a 'W' shape");
        if (!pinkyDown) hints.push("Keep your pinky finger tucked");
        return { match: threeUp && spread && pinkyDown, hints };
    }

    isLetterX(hand) {
        const indexHooked = hand[8].y > hand[6].y && hand[8].y < hand[5].y;
        const othersClosed = [12, 16, 20].every(tip => hand[tip].y > hand[tip - 1].y);
        const hints = [];
        if (!indexHooked) hints.push("Hook your index finger like a claw");
        if (!othersClosed) hints.push("Keep other fingers closed");
        return { match: indexHooked && othersClosed, hints };
    }

    isLetterY(hand) {
        const thumbOut = Math.abs(hand[4].x - hand[2].x) > 0.15;
        const pinkyUp = hand[20].y < hand[18].y;
        const middleCurled = [8, 12, 16].every(tip => hand[tip].y > hand[tip - 1].y);
        const hints = [];
        if (!thumbOut || !pinkyUp) hints.push("Extend your thumb and pinky out");
        if (!middleCurled) hints.push("Keep middle fingers curled tightly");
        return { match: thumbOut && pinkyUp && middleCurled, hints };
    }

    isLetterZ(hand) {
        // Static pose same as Index Up for now
        const indexUp = hand[8].y < hand[6].y;
        const othersClosed = [12, 16, 20].every(tip => hand[tip].y > hand[tip - 2].y);
        const hints = [];
        if (!indexUp) hints.push("Point your index finger up");
        return { match: indexUp && othersClosed, hints };
    }

    // LETTER A: Fist, thumb on side
    isLetterA(hand) {
        const fingersCurled = [8, 12, 16, 20].every(tip => hand[tip].y > hand[tip - 2].y);
        const thumbSide = hand[4].y < hand[3].y && hand[4].x > hand[5].x;
        const hints = [];
        if (!fingersCurled) hints.push("Close your hand into a tight fist");
        if (!thumbSide) hints.push("Tuck your thumb against your index finger");
        return { match: fingersCurled && thumbSide, hints };
    }

    // LETTER C: Hand curved into a 'C' shape
    isLetterC(hand) {
        const indexCurved = hand[8].y < hand[6].y && hand[8].y > hand[5].y + 0.05;
        const middleCurved = hand[12].y < hand[10].y && hand[12].y > hand[9].y + 0.05;
        const dist = Math.sqrt(Math.pow(hand[4].x - hand[8].x, 2) + Math.pow(hand[4].y - hand[8].y, 2));
        const match = indexCurved && middleCurved && dist > 0.15 && dist < 0.4;
        const hints = [];
        if (!indexCurved || !middleCurved) hints.push("Curve your fingers forward");
        if (dist < 0.15) hints.push("Open your 'C' shape wider");
        if (dist > 0.45) hints.push("Bring your thumb and fingers closer");
        return { match, hints };
    }

    // Draw the video frame and optional ghost overlay onto the canvas
    drawVideo(ctx, video, ghostImg = null) {
        if (!video || video.readyState < 2) return;

        // 1. Draw live video feed
        ctx.drawImage(video, 0, 0, ctx.canvas.width, ctx.canvas.height);

        // 2. Draw Ghost Overlay if provided
        if (ghostImg && ghostImg.complete) {
            ctx.save();
            ctx.globalAlpha = 0.3; // Make it ghostly
            ctx.filter = "blur(2px)"; // Slight blur for guidance

            // Calculate aspect-fit dimensions for the ghost image
            const aspect = ghostImg.width / ghostImg.height;
            let drawW = ctx.canvas.width;
            let drawH = drawW / aspect;

            if (drawH > ctx.canvas.height) {
                drawH = ctx.canvas.height;
                drawW = drawH * aspect;
            }

            const x = (ctx.canvas.width - drawW) / 2;
            const y = (ctx.canvas.height - drawH) / 2;

            ctx.drawImage(ghostImg, x, y, drawW, drawH);
            ctx.restore();
        }
    }

    drawLandmarks(ctx, results) {
        if (!results || !results.landmarks) return;

        for (const landmarks of results.landmarks) {
            // Draw connections
            this.drawConnectors(ctx, landmarks);
            // Draw points
            for (const landmark of landmarks) {
                ctx.beginPath();
                ctx.arc(landmark.x * ctx.canvas.width, landmark.y * ctx.canvas.height, 3, 0, 2 * Math.PI);
                ctx.fillStyle = "#00f2fe";
                ctx.fill();
            }
        }
    }

    drawConnectors(ctx, landmarks) {
        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4], // thumb
            [0, 5], [5, 6], [6, 7], [7, 8], // index
            [5, 9], [9, 10], [10, 11], [11, 12], // middle
            [9, 13], [13, 14], [14, 15], [15, 16], // ring
            [13, 17], [17, 18], [18, 19], [19, 20], // pinky
            [0, 17] // palm
        ];

        ctx.strokeStyle = "rgba(0, 242, 254, 0.5)";
        ctx.lineWidth = 2;
        for (const [start, end] of connections) {
            ctx.beginPath();
            ctx.moveTo(landmarks[start].x * ctx.canvas.width, landmarks[start].y * ctx.canvas.height);
            ctx.lineTo(landmarks[end].x * ctx.canvas.width, landmarks[end].y * ctx.canvas.height);
            ctx.stroke();
        }
    }
}

// Load MediaPipe using FilesetResolver for stability
import { HandLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0";

window.AIGestureEngine = new AIGestureEngine();
