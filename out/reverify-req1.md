# Dafny re-verification plan

## Changed symbols

- DispatcherModel.Dispatcher.DispatchOne                  contract
- DispatcherModel.Dispatcher.Drain                        contract
- DispatcherModel.Dispatcher.EvictOldestNonCritical       contract
- DispatcherModel.Dispatcher.Submit                       contract
- DispatcherModel.Dispatcher.Valid                        definition
- DispatcherModel.Dispatcher._ctor                        contract
- RingQueueModel.RingQueue.Clear                          contract
- RingQueueModel.RingQueue.Grow                           added
- RingQueueModel.RingQueue.Inv                            definition
- RingQueueModel.RingQueue.MaxCapacity                    added
- RingQueueModel.RingQueue.Offer                          contract
- RingQueueModel.RingQueue.Poll                           contract
- RingQueueModel.RingQueue.Valid                          definition
- RingQueueModel.RingQueue._ctor                          contract

## Must be re-verified: 19 of 51 symbols

- DispatcherModel.Dispatcher.DispatchOne                  <- calls RingQueue.Poll (contract changed); contract changed; mentions Dispatcher.Valid (definition changed)
- DispatcherModel.Dispatcher.Drain                        <- calls Dispatcher.DispatchOne (contract changed); contract changed; mentions Dispatcher.Valid (definition changed)
- DispatcherModel.Dispatcher.EvictOldestNonCritical       <- calls RingQueue.Offer (contract changed); calls RingQueue.Poll (contract changed); contract changed; mentions Dispatcher.Valid (definition changed)
- DispatcherModel.Dispatcher.Submit                       <- calls Dispatcher.DispatchOne (contract changed); calls Dispatcher.EvictOldestNonCritical (contract changed); calls RingQueue.Offer (contract changed); contract changed; mentions Dispatcher.Valid (definition changed)
- DispatcherModel.Dispatcher.Valid                        <- definition changed; mentions RingQueue.MaxCapacity (definition changed)
- DispatcherModel.Dispatcher._ctor                        <- contract changed; mentions RingQueue.MaxCapacity (definition changed)
- RingQueueModel.RingQueue.Clear                          <- calls RingQueue.Poll (contract changed); contract changed; mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.GetCapacity                    <- mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Grow                           <- added; mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Inv                            <- definition changed
- RingQueueModel.RingQueue.IsEmpty                        <- mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.MaxCapacity                    <- added; definition changed
- RingQueueModel.RingQueue.Offer                          <- contract changed; mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Peek                           <- mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Poll                           <- contract changed; mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Size                           <- mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Snapshot                       <- mentions RingQueue.Inv (definition changed)
- RingQueueModel.RingQueue.Valid                          <- definition changed; mentions RingQueue.MaxCapacity (definition changed)
- RingQueueModel.RingQueue._ctor                          <- contract changed; mentions RingQueue.MaxCapacity (definition changed)

## Java impact analysis vs. Dafny proof dependencies

Dafny symbols suggested by the Java impact set (changed + impacted, mapped): 21

In the Java impact set but NO re-verification needed (modular proofs): 8
- PowerBudgetModel.PowerBudget.Headroom
- PowerBudgetModel.PowerBudget.IsIdle
- PowerBudgetModel.PowerBudget.IsRunning
- PowerBudgetModel.PowerBudget.Stop
- PowerBudgetModel.PowerBudget.StopAll
- PowerBudgetModel.PowerBudget.TotalLoad
- PowerBudgetModel.PowerBudget.TryStart
- PowerBudgetModel.PowerBudget._ctor

Needs re-verification but NOT in the Java impact set (spec-only dependencies, e.g. a function used in contracts): 6
- DispatcherModel.Dispatcher.Valid
- DispatcherModel.Dispatcher._ctor
- RingQueueModel.RingQueue.Grow
- RingQueueModel.RingQueue.Inv
- RingQueueModel.RingQueue.MaxCapacity
- RingQueueModel.RingQueue.Valid

## Verification cost

full      :   1.7s wall | Dafny program verifier finished with 73 verified, 0 errors
selective :   2.3s wall | 2 dafny run(s), 6 extra symbol(s) verified by module runs

prover work (from the full run's log, start-up excluded):
  all symbols     :   1.65s solver time,      4765720 resource units
  selected only   :   1.04s solver time,      3335499 resource units (70%)
