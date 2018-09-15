require('json')

class ActionMapData
  @@action_map_file_path = 'action_map.json'

  class << self
    def fetch
      JSON.parse(File.read(@@action_map_file_path))
    end

    # Em không biết có nên dùng database thay cho json khi cần CURD không?
    # Vào DB thì việc đồng bộ các server, đảm bảo ACID có vẻ dễ hơn???
    #
    # Vào DB thì có thể cập nhật cả json hoặc cập nhật từng key(like, dislike...) tùy theo cách mình lưu dữ liệu,
    # và dữ liệu nhiều hay ít.
    #
    # Vì không viết có cần chuyển vào DB trong tương lai hay không => để tách biệt logic + đối ứng sự thay đổi đó,
    # em tách việc đọc json(hiện tại) ra thành 1 class riêng, và đổi tên thành fetch.
    def update(action_maps)
      File.write(@@action_map_file_path, JSON.pretty_generate(action_maps))
    end
  end
end


class Test
  class << self
    def init
      @@action_map ||= ActionMapData.fetch()
    end

    def action(verb)
      @@action_map[verb]
    end

    def delete_action(verbs)
      # @@action_map.except(verbs)
      verbs.map {|verb| @@action_map.delete(verb)}
      ActionMapData.update(@@action_map)
    end

    # Em không biết dùng observer pattern cho biến @@action_map, nên em đành viết như dưới, gọi thủ công ạ :(
    def add_action(action_map)
      update_action(action_map)
    end

    def update_action(action_map)
      @@action_map.merge!(action_map)
      ActionMapData.update(@@action_map)
    end

    def available_action()
      puts @@action_map.keys
    end
  end

  init
end


puts Test.action('like')
Test.delete_action(%w(like dislike))
# puts Test.available_action


Test.add_action({"add_action__test_1" => '🙇'})
puts Test.action("add_action__test_1")
# puts Test.available_action


Test.update_action({"add_action__test_1" => '💃'})
puts Test.action("add_action__test_1")
# puts Test.available_action


Test.delete_action(["add_action__test_1"])
# puts Test.available_action
