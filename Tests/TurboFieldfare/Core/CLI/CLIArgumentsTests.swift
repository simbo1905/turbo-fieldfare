import Testing
@testable import TurboFieldfareCLICore

@Suite struct CLIArgumentsTests {
    @Test func defaultsUseGemmaSummaryProfileValues() throws {
        let arguments = try Args.parse(["--model", "m.gturbo", "--prompt", "hi"])
        #expect(arguments.model == "m.gturbo")
        #expect(arguments.prompt == "hi")
        #expect(arguments.messagesFile == nil)
        #expect(arguments.maxNew == Args.remainingContext)
        #expect(arguments.maxContext == 4096)
        #expect(arguments.temperature == 0.2)
        #expect(arguments.topK == 64)
        #expect(arguments.topP == 0.95)
        #expect(arguments.repetitionPenalty == 1.0)
        #expect(arguments.seed == nil)
        #expect(arguments.stops.isEmpty)
        #expect(!arguments.quiet)
    }

    @Test func generationOptionsParseAndStopsRepeat() throws {
        let arguments = try Args.parse([
            "--model", "m.gturbo", "--prompt", "hi",
            "--max-new", "32", "--max-context", "4096",
            "--temperature", "0", "--top-k", "40", "--top-p", "0.95",
            "--repetition-penalty", "1.1", "--seed", "42",
            "--stop", "A", "--stop", "B", "--quiet",
        ])
        #expect(arguments.maxNew == 32)
        #expect(arguments.maxContext == 4096)
        #expect(arguments.temperature == 0)
        #expect(arguments.topK == 40)
        #expect(arguments.topP == 0.95)
        #expect(arguments.repetitionPenalty == 1.1)
        #expect(arguments.seed == 42)
        #expect(arguments.stops == ["A", "B"])
        #expect(arguments.quiet)
    }

    @Test func acceptsOnlyDocumentedContextLengths() throws {
        for context in Args.supportedContexts {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--max-context", "\(context)",
            ])
            #expect(arguments.maxContext == context)
        }
        #expect(throws: ArgsError.invalidValue(flag: "--max-context", value: "512")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--max-context", "512"])
        }
    }

    @Test func maxNewAcceptsAnyPositiveRequestedLimit() throws {
        for maxNew in [1, 32, 1_024] {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--max-new", "\(maxNew)",
            ])
            #expect(arguments.maxNew == maxNew)
        }
    }

    @Test func topKZeroRequiresTopPToBeDisabled() throws {
        let disabled = try Args.parse([
            "--model", "m.gturbo", "--prompt", "hi",
            "--top-k", "0", "--top-p", "1",
        ])
        #expect(disabled.topK == nil)
        #expect(disabled.topP == 1)

        #expect(throws: ArgsError.self) {
            _ = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--top-k", "0",
            ])
        }
    }

    @Test func topKAboveKernelLimitRejected() {
        #expect(throws: ArgsError.invalidValue(flag: "--top-k", value: "257")) {
            _ = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--top-k", "257",
            ])
        }
    }

    @Test func helpListsExactlyThePublicOptions() {
        let expected: Set<String> = [
            "--model", "--prompt", "--messages-file", "--max-new", "--max-context",
            "--temperature", "--top-k", "--top-p", "--repetition-penalty",
            "--seed", "--stop", "--quiet",
            "--expert-cache-slots", "--expert-cache-policy",
            "--prefill", "--prefill-chunk-tokens", "--rdadvise",
            "--help",
        ]
        let words = Args.usage.split { $0.isWhitespace || $0 == "(" || $0 == ")" }
        let options = Set(words.map(String.init).filter { $0.hasPrefix("--") })
        #expect(options == expected)
    }

    @Test func unsupportedSelectorsAreRejected() {
        for flag in ["--runtime-profile", "--experiment-id", "-h"] {
            #expect(throws: ArgsError.unknownFlag(flag)) {
                _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", flag])
            }
        }
    }

    @Test func modelAndPromptAreRequired() {
        #expect(throws: ArgsError.requiredMissing("--model")) {
            _ = try Args.parse(["--prompt", "hi"])
        }
        #expect(throws: ArgsError.modeMissing) {
            _ = try Args.parse(["--model", "m.gturbo"])
        }
    }

    @Test func messagesFileSelectsChatMode() throws {
        let arguments = try Args.parse([
            "--model", "m.gturbo", "--messages-file", "chat.json",
        ])
        #expect(arguments.prompt == nil)
        #expect(arguments.messagesFile == "chat.json")
    }

    @Test func promptAndMessagesFileAreMutuallyExclusive() {
        #expect(throws: ArgsError.mutuallyExclusive("--prompt", "--messages-file")) {
            _ = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi",
                "--messages-file", "chat.json",
            ])
        }
    }

    @Test func expertCacheSlotsAcceptsAllowedValues() throws {
        for slots in [8, 16, 24, 32] {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--expert-cache-slots", "\(slots)",
            ])
            #expect(arguments.expertCacheSlots == slots)
        }
        #expect(throws: ArgsError.invalidValue(flag: "--expert-cache-slots", value: "7")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--expert-cache-slots", "7"])
        }
    }

    @Test func expertCachePolicyAcceptsAllowedValues() throws {
        for policy in ["lfu", "lru"] {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--expert-cache-policy", policy,
            ])
            #expect(arguments.expertCachePolicy == policy)
        }
        #expect(throws: ArgsError.invalidValue(flag: "--expert-cache-policy", value: "fifo")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--expert-cache-policy", "fifo"])
        }
    }

    @Test func prefillAcceptsOnOrOff() throws {
        let on = try Args.parse([
            "--model", "m.gturbo", "--prompt", "hi", "--prefill", "on",
        ])
        #expect(on.prefillEnabled)
        let off = try Args.parse([
            "--model", "m.gturbo", "--prompt", "hi", "--prefill", "off",
        ])
        #expect(!off.prefillEnabled)
        #expect(throws: ArgsError.invalidValue(flag: "--prefill", value: "yes")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--prefill", "yes"])
        }
    }

    @Test func prefillChunkTokensAcceptsAllowedValues() throws {
        for tokens in [32, 64, 128] {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--prefill-chunk-tokens", "\(tokens)",
            ])
            #expect(arguments.prefillChunkTokens == tokens)
        }
        #expect(throws: ArgsError.invalidValue(flag: "--prefill-chunk-tokens", value: "256")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--prefill-chunk-tokens", "256"])
        }
    }

    @Test func rdadviseAcceptsAllowedValues() throws {
        for policy in ["off", "default", "bounded", "adaptive"] {
            let arguments = try Args.parse([
                "--model", "m.gturbo", "--prompt", "hi", "--rdadvise", policy,
            ])
            #expect(arguments.rdadvisePolicy == policy)
        }
        #expect(throws: ArgsError.invalidValue(flag: "--rdadvise", value: "aggressive")) {
            _ = try Args.parse(["--model", "m.gturbo", "--prompt", "hi", "--rdadvise", "aggressive"])
        }
    }

    @Test func runtimeFlagsDefaultToProductionValues() throws {
        let arguments = try Args.parse(["--model", "m.gturbo", "--prompt", "hi"])
        #expect(arguments.expertCacheSlots == 16)
        #expect(arguments.expertCachePolicy == "lfu")
        #expect(arguments.prefillEnabled)
        #expect(arguments.prefillChunkTokens == 128)
        #expect(arguments.rdadvisePolicy == "off")
    }
}
