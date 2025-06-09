def extract_top_keywords(user_id):
    """
    사용자별 상위 5개 키워드 추출 노드
    context['user_id'] 필요, context['keywords']에 결과 저장
    """
    from app.services.interest_service import InterestService
    interest_service = InterestService()
    top_interests = sorted(
        interest_service.get_interests_by_user(user_id),
        key=lambda i: i.importance,
        reverse=True
    )[:5]
    keywords = [i.content for i in top_interests]
    interest_ids = [str(i.id) for i in top_interests]
    return {"keywords": keywords, "interest_ids": interest_ids}
