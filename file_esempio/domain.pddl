;; domain.pddl
(define (domain chiave-drago)
  (:requirements :strips :typing :negative-preconditions)
  (:types
    entity drago luogo
    eroe principessa artefatto - entity
  )

  (:predicates
    (at ?x - entity ?l - luogo)       ;; posizione di eroe/principessa/chiave
    (alive ?d - drago)                ;; il drago è vivo
    (sealed ?d - drago)               ;; il drago è sigillato
    (rescued ?p - principessa)        ;; la principessa è stata salvata
    (skeleton-guarded ?l - luogo)     ;; presenza di scheletri in una location
    (bridge-intact)                   ;; lo stato del ponte
    (has-key ?e - eroe)               ;; l’eroe possiede la chiave
  )

  ;; Movimento tra luoghi adiacenti
  (:action move
    :parameters (?e - eroe ?from ?to - luogo)
    :precondition (at ?e ?from)
    :effect (and (not (at ?e ?from)) (at ?e ?to))
  )

  ;; Combattere e sconfiggere gli scheletri
  (:action fight-skeletons
    :parameters (?e - eroe ?l - luogo)
    :precondition (and (at ?e ?l) (skeleton-guarded ?l))
    :effect (and (not (skeleton-guarded ?l)))
  )

  ;; Attraversare il ponte (lo rompe)
  (:action cross-bridge
    :parameters (?e - eroe ?from ?to - luogo)
    :precondition (and (at ?e ?from) (bridge-intact))
    :effect (and (not (at ?e ?from)) (at ?e ?to) (not (bridge-intact)))
  )

  ;; Recuperare la Chiave di Luce
  (:action retrieve-key
    :parameters (?e - eroe ?a - artefatto ?l - luogo)
    :precondition (and (at ?e ?l) (at ?a ?l))
    :effect (and (has-key ?e) (not (at ?a ?l)))
  )

  ;; Salvare la principessa
  (:action rescue-princess
    :parameters (?e - eroe ?p - principessa ?l - luogo)
    :precondition (and (at ?e ?l) (at ?p ?l))
    :effect (and (rescued ?p))
  )

  ;; Sigillare il drago con la chiave
  (:action seal-dragon
    :parameters (?e - eroe ?d - drago)
    :precondition (and (has-key ?e) (alive ?d))
    :effect (and (sealed ?d) (not (alive ?d)))
  )
)
